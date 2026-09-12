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

#endif /* ATARISANDBOX_ANALYSIS_H */
