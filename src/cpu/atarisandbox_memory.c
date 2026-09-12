/*
 * AtariSandbox - Hatari Malware Analysis Edition
 *
 * Passive guest-memory write instrumentation. This file is distributed under
 * the same GPL-2.0-or-later terms as Hatari; see gpl.txt.
 */
#include "sysdeps.h"
#include "atarisandbox_analysis.h"

void AtariSandbox_real_memory_put_long(uaecptr addr, uae_u32 value);
void AtariSandbox_real_memory_put_word(uaecptr addr, uae_u32 value);
void AtariSandbox_real_memory_put_byte(uaecptr addr, uae_u32 value);

void memory_put_long(uaecptr addr, uae_u32 value)
{
	AtariAnalysis_RecordMemoryWrite((uint32_t)addr, 4, (uint32_t)value);
	AtariSandbox_real_memory_put_long(addr, value);
}

void memory_put_word(uaecptr addr, uae_u32 value)
{
	AtariAnalysis_RecordMemoryWrite((uint32_t)addr, 2, (uint32_t)(value & 0xffff));
	AtariSandbox_real_memory_put_word(addr, value);
}

void memory_put_byte(uaecptr addr, uae_u32 value)
{
	AtariAnalysis_RecordMemoryWrite((uint32_t)addr, 1, (uint32_t)(value & 0xff));
	AtariSandbox_real_memory_put_byte(addr, value);
}
