/*
 * AtariSandbox - Hatari Malware Analysis Edition
 *
 * Passive defensive-analysis instrumentation.  This file is distributed
 * under the same GPL-2.0-or-later terms as Hatari; see gpl.txt.
 */
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "atarisandbox_analysis.h"
#include "m68000.h"

static FILE *AnalysisEvents;
static int AnalysisInitDone;
static int MemoryConfigDone;
static uint64_t MemoryWriteLimit;
static uint64_t MemoryWriteCount;
static uint32_t WatchStart;
static uint32_t WatchEnd = UINT32_MAX;
static int MediaConfigDone;
static uint64_t MediaIOLimit;
static uint64_t MediaIOCount;

static FILE *AtariAnalysis_Open(void)
{
	const char *dir;
	char path[FILENAME_MAX];

	if (AnalysisInitDone)
		return AnalysisEvents;
	AnalysisInitDone = 1;

	dir = getenv("ATARISANDBOX_ANALYSIS_DIR");
	if (!dir || !*dir)
		return NULL;

	if (snprintf(path, sizeof(path), "%s/core-events.jsonl", dir) >= (int)sizeof(path))
		return NULL;

	AnalysisEvents = fopen(path, "a");
	if (AnalysisEvents)
		setvbuf(AnalysisEvents, NULL, _IOLBF, 0);
	return AnalysisEvents;
}

static void AtariAnalysis_LoadMemoryConfig(void)
{
	const char *value;
	char *endptr;
	unsigned long long parsed;

	if (MemoryConfigDone)
		return;
	MemoryConfigDone = 1;

	value = getenv("ATARISANDBOX_MEMORY_WRITE_LIMIT");
	if (value && *value) {
		parsed = strtoull(value, &endptr, 0);
		if (*endptr == '\0')
			MemoryWriteLimit = (uint64_t)parsed;
	}

	value = getenv("ATARISANDBOX_WATCH_START");
	if (value && *value) {
		parsed = strtoull(value, &endptr, 0);
		if (*endptr == '\0' && parsed <= UINT32_MAX)
			WatchStart = (uint32_t)parsed;
	}

	value = getenv("ATARISANDBOX_WATCH_END");
	if (value && *value) {
		parsed = strtoull(value, &endptr, 0);
		if (*endptr == '\0' && parsed <= UINT32_MAX)
			WatchEnd = (uint32_t)parsed;
	}
}

static void AtariAnalysis_LoadMediaConfig(void)
{
	const char *value;
	char *endptr;
	unsigned long long parsed;

	if (MediaConfigDone)
		return;
	MediaConfigDone = 1;
	value = getenv("ATARISANDBOX_MEDIA_IO_LIMIT");
	if (value && *value) {
		parsed = strtoull(value, &endptr, 0);
		if (*endptr == '\0')
			MediaIOLimit = (uint64_t)parsed;
	}
}

void AtariAnalysis_RecordException(uint32_t exception_nr, int exception_source)
{
	FILE *fp = AtariAnalysis_Open();
	uint64_t unix_ns;
	int i;

	if (!fp)
		return;

	unix_ns = (uint64_t)time(NULL) * UINT64_C(1000000000);
	MakeSR();

	fprintf(fp,
	        "{\"schema\":\"atarisandbox.event/1\","
	        "\"type\":\"cpu.exception.snapshot\","
	        "\"source\":\"atarisandbox.cpu_core\","
	        "\"unix_ns\":%" PRIu64 ","
	        "\"exception_nr\":%" PRIu32 ","
	        "\"exception_source\":%d,"
	        "\"pc\":%" PRIu32 ","
	        "\"instruction_pc\":%" PRIu32 ","
	        "\"sr\":%u,"
	        "\"cycles\":%" PRIi64 ","
	        "\"d\":[",
	        unix_ns, exception_nr, exception_source,
	        (uint32_t)M68000_GetPC(), (uint32_t)M68000_InstrPC,
	        (unsigned int)regs.sr, (int64_t)nCyclesMainCounter);

	for (i = REG_D0; i <= REG_D7; i++)
		fprintf(fp, "%s%" PRIu32, i == REG_D0 ? "" : ",", (uint32_t)Regs[i]);
	fputs("],\"a\":[", fp);
	for (i = REG_A0; i <= REG_A7; i++)
		fprintf(fp, "%s%" PRIu32, i == REG_A0 ? "" : ",", (uint32_t)Regs[i]);
	fputs("]}\n", fp);
	fflush(fp);
}

void AtariAnalysis_RecordMemoryWrite(uint32_t address, uint32_t size, uint32_t value)
{
	FILE *fp;
	uint64_t unix_ns;

	AtariAnalysis_LoadMemoryConfig();
	if (!MemoryWriteLimit || MemoryWriteCount >= MemoryWriteLimit)
		return;
	if (address < WatchStart || address > WatchEnd)
		return;
	if (size > 1 && address > WatchEnd - (size - 1))
		return;

	fp = AtariAnalysis_Open();
	if (!fp)
		return;

	MemoryWriteCount++;
	unix_ns = (uint64_t)time(NULL) * UINT64_C(1000000000);
	fprintf(fp,
	        "{\"schema\":\"atarisandbox.event/1\","
	        "\"type\":\"memory.write\","
	        "\"source\":\"atarisandbox.memory_core\","
	        "\"unix_ns\":%" PRIu64 ","
	        "\"address\":%" PRIu32 ","
	        "\"size\":%" PRIu32 ","
	        "\"value\":%" PRIu32 ","
	        "\"pc\":%" PRIu32 ","
	        "\"instruction_pc\":%" PRIu32 ","
	        "\"cycles\":%" PRIi64 "}\n",
	        unix_ns, address, size, value,
	        (uint32_t)M68000_GetPC(), (uint32_t)M68000_InstrPC,
	        (int64_t)nCyclesMainCounter);
	fflush(fp);
}

void AtariAnalysis_RecordFloppyIO(const char *operation, int drive,
                                  uint16_t sector, uint16_t track,
                                  uint16_t side, short count,
                                  uint32_t sector_size)
{
	FILE *fp;
	uint64_t unix_ns;
	uint32_t sectors;
	int boot_sector;

	AtariAnalysis_LoadMediaConfig();
	if (!MediaIOLimit || MediaIOCount >= MediaIOLimit)
		return;
	fp = AtariAnalysis_Open();
	if (!fp)
		return;

	MediaIOCount++;
	sectors = count < 0 ? 0 : (uint32_t)count;
	boot_sector = operation && strcmp(operation, "write") == 0 &&
	              track == 0 && side == 0 && sector == 1;
	unix_ns = (uint64_t)time(NULL) * UINT64_C(1000000000);
	fprintf(fp,
	        "{\"schema\":\"atarisandbox.event/1\","
	        "\"type\":\"media.floppy.%s\","
	        "\"source\":\"atarisandbox.floppy_core\","
	        "\"unix_ns\":%" PRIu64 ","
	        "\"drive\":%d,\"track\":%u,\"side\":%u,\"sector\":%u,"
	        "\"count\":%" PRIu32 ",\"sector_size\":%" PRIu32 ","
	        "\"boot_sector\":%s}\n",
	        operation ? operation : "unknown", unix_ns, drive,
	        (unsigned int)track, (unsigned int)side, (unsigned int)sector,
	        sectors, sector_size, boot_sector ? "true" : "false");
	fflush(fp);
}

#ifdef ATARISANDBOX_LD_WRAP_EXCEPTION
extern void __real_M68000_Exception(uint32_t exception_nr, int exception_source);

void __wrap_M68000_Exception(uint32_t exception_nr, int exception_source)
{
	AtariAnalysis_RecordException(exception_nr, exception_source);
	__real_M68000_Exception(exception_nr, exception_source);
}
#endif
