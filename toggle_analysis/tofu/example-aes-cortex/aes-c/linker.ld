ENTRY(_start)

MEMORY
{
    rom (rx) : ORIGIN = 0x08000000, LENGTH = 256K
    ram (rwx) : ORIGIN = 0x20000000, LENGTH = 16K
}

SECTIONS
{
    .text : { *(.text*) } > rom
    .rodata : { *(.rodata*) } > rom
    .bss : { *(.bss*) } > ram
} 