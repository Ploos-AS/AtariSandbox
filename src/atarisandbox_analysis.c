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

void AtariAnalysis_RecordException(uint32_t exception_nr, int exception_source)
{
	FILE *fp = AtariAnalysis_Open();
	uint64_t unix_ns;
	int i;

	if (!fp)
		return;

	unix_ns = (uint64_t)time(NULL) * UINT64_C(1000000000);

	/* Make SR current before serializing the passive snapshot. */
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
	        unix_ns,
	        exception_nr,
	        exception_source,
	        (uint32_t)M68000_GetPC(),
	        (uint32_t)M68000_InstrPC,
	        (unsigned int)regs.sr,
	        (int64_t)nCyclesMainCounter);

	for (i = REG_D0; i <= REG_D7; i++)
		fprintf(fp, "%s%" PRIu32, i == REG_D0 ? "" : ",", (uint32_t)Regs[i]);

	fputs("],\"a\":[", fp);
	for (i = REG_A0; i <= REG_A7; i++)
		fprintf(fp, "%s%" PRIu32, i == REG_A0 ? "" : ",", (uint32_t)Regs[i]);

	fputs("]}\n", fp);
	fflush(fp);
}

/*
 * GNU/ELF link-time wrapping lets AtariSandbox observe the existing Hatari
 * exception entry point without changing Hatari's exception semantics.
 * Builds that do not enable the linker wrapper still compile the passive
 * recorder, but never route normal Hatari execution through this function.
 */
#ifdef ATARISANDBOX_LD_WRAP_EXCEPTION
extern void __real_M68000_Exception(uint32_t exception_nr, int exception_source);

void __wrap_M68000_Exception(uint32_t exception_nr, int exception_source)
{
	AtariAnalysis_RecordException(exception_nr, exception_source);
	__real_M68000_Exception(exception_nr, exception_source);
}
#endif
