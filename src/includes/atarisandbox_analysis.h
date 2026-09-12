/*
 * AtariSandbox - Hatari Malware Analysis Edition
 *
 * Defensive analysis instrumentation.  This file is distributed under the
 * same GPL-2.0-or-later terms as Hatari; see gpl.txt.
 */
#ifndef ATARISANDBOX_ANALYSIS_H
#define ATARISANDBOX_ANALYSIS_H

#include <stdint.h>

/*
 * Record an exception/interrupt request with a passive CPU snapshot.
 * The implementation is a no-op unless ATARISANDBOX_ANALYSIS_DIR is set.
 */
void AtariAnalysis_RecordException(uint32_t exception_nr, int exception_source);

/*
 * Record a guest-visible memory write. Logging is disabled unless
 * ATARISANDBOX_MEMORY_WRITE_LIMIT is a positive integer. Optional
 * ATARISANDBOX_WATCH_START/ATARISANDBOX_WATCH_END bounds select a guest
 * address range (inclusive).
 */
void AtariAnalysis_RecordMemoryWrite(uint32_t address, uint32_t size, uint32_t value);

#endif /* ATARISANDBOX_ANALYSIS_H */
