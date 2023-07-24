---
template: "post.html.j2"
title: "A Beginner's Guide to x86 Assembly, Part 1 of 2"
date: 2017-02-12
summary: "In this two-part series we will be implementing a Reverse Polish notation (RPN) calculator in bare x86 assembly from the ground up."
---

This was originally submitted to Reddit [here](https://www.reddit.com/r/programming/comments/9cx127/a_beginners_guide_to_x86_assembly_writing_a/).

Writing bare assembly is rarely necessary these days, but I definitely recommend it for anyone interested in programming. Not only does it offer a different perspective compared to higher-level languages, but it may prove to be useful when debugging code in other languages.

In this two-part series we will be implementing a [Reverse Polish notation (RPN)](https://en.wikipedia.org/wiki/Reverse_Polish_notation) calculator in bare x86 assembly from the ground up. When we're done we'll be able to use it like this:

```bash
$ ./calc "32+6*" # "(3+2)*6" in infix notation
30
```

The complete code from the end of Part 1 can be found [here](https://gist.github.com/gurchik/79dca38ccc2a5e263d0635f1b7737ec9). Additionally, if you feel like taking a peek, the complete code from the end of this series can be found [here](https://gist.github.com/gurchik/9dff75a67710207e16cd6a8531393ccf). It is heavily commented and these two may serve as a sufficient learning resource for those of you with some knowledge of assembly already.

In Part 1 we will begin with a basic "Hello world!" program to ensure your setup is working properly. We will progress to explaining system calls, call stack, stack frames, and the x86 calling convention. We will then finish by writing some basic functions in x86 assembly for practice. In Part 2 we we will begin our RPN calculator from scratch.

This article series is aimed at people who have some experience programming in C and have some basic knowledge of computer architecture (such as what a CPU register is). Since we will be using Linux you will also need to know how to use the Linux command line.


## Setup

As stated before, we will be using Linux (either 64-bit or 32-bit). The code in this article series will not work on Windows or Mac OS X.

You simply need the GNU linker `ld` from `binutils`, which is pre-installed on most distros, and the NASM assembler. On Ubuntu and Debian you can install both with:

```bash
$ sudo apt-get install binutils nasm
```

I would also recommend you keep an [ASCII table](http://www.asciitable.com/) handy.


## Hello world

To ensure your setup is ready to begin, save the following code into a file called `calc.asm`:

```nasm
; Allow the linker to find the _start symbol. The linker will begin program execution
; there.
global _start

; Start the .rodata section of the executable, which stores constants (read only data)
; It doesn't matter which order your sections are in, I just like putting .data first
section .rodata
    ; Declare some bytes at a symbol called hello_world. NASM's db pseudo-instruction
    ; allows either a single byte value, a constant string, or a combination of the two
    ; as seen here. 0xA = new line, and 0x0 = string-terminating null
    hello_world: db "Hello world!", 0xA, 0x0

; Start the .text section, which stores program code
section .text
_start:
    mov eax, 0x04           ; store the number 4 in the eax register (0x04 = write())
    mov ebx, 0x1            ; file descriptor (1 = standard output, 2 = standard error)
    mov ecx, hello_world    ; pointer to the string we're printing
    mov edx, 14             ; length of the string
    int 0x80                ; send the interrupt signal 0x80 which the OS interprets as
                            ;   a syscall

    mov eax, 0x01           ; 0x01 = exit()
    mov ebx, 0              ; 0 = no errors
    int 0x80
```

The comments should explain the general strucure, but you are probably a bit confused on how it works. If you are confused about the instructions or the registers used, you can reference [University of Virginia's Guide to x86 Assembly](http://www.cs.virginia.edu/~evans/cs216/guides/x86.html) for a list of registers and common instructions. Once we discuss system calls this should hopefully make even more sense.

To assemble the assembly file into an object file, then to link the object file into an executable, run:

```bash
$ nasm -f elf_i386 calc.asm -o calc
$ ld -m elf_i386 calc.o -o calc
```

When run you should see:

```bash
$ ./calc
Hello world!
```

### Makefile

This part is optional, but to easily assemble and link in the future, we can create use Make. Save the following into a file called `Makefile` in the same directory as your `calc.asm` file:

```makefile
CFLAGS= -f elf32
LFLAGS= -m elf_i386

all: calc

calc: calc.o
	ld $(LFLAGS) calc.o -o calc

calc.o: calc.asm
	nasm $(CFLAGS) calc.asm -o calc.o

clean:
	rm -f calc.o calc

.INTERMEDIATE: calc.o
```

Then to assemble and link, instead of following the above instructions, you can simply run `make`.


## System calls

System calls are used to request the operating system to perform an action for us. System calls are set up by storing the system call number in register `eax`, followed by its arguments in `ebx`, `ecx`, `edx` in that order (if applicable). If a system call does not use a particular argument than that register can be set to anything. For example, if a system call only takes 1 argument, then the values in `ecx` and `edx` will be ignored.

```
eax = syscall number
ebx = arg1
ecx = arg2
edx = arg3
```

In this article, we will only be using the following two system calls[^1]: `write()`, which writes a string to a file or stream (in our case, to standard out and standard error), and `exit()`, to exit the program:

[^1]: If interested you may find a reference for more Linux system calls [here](http://syscalls.kernelgrok.com/).

* `exit` (syscall number `0x01`): Exits the program. Arguments:
  * `error code` - set to 0 to indicate the program ended without errors, and use any other number (such as 1) to instead indicate an error occurred
* `write` (syscall number `0x04`): Writes a string to a file or stream. Arguments:
  * `fd` - The number of an open file descriptor for the file to write to. In our case, we will use 1 to write to standard output and 2 for standard error output.
  * `string` - a pointer to the first character of the string
  * `length` - the length of the string in bytes

## The call stack

The call stack is a data structure that stores information about each function call. Each function call has its own section in the stack called a "frame," which stores some information about the current function call, such as the local variables of that function and the return address (where the program should jump to once the function is done executing).

<figure>
  <img src="/images/2017/beginners-assembly/callstack.png">
  <figcaption>
    <p>Fig. 1: The call stack</p>
  </figcaption>
</figure>

One confusing thing that I will note immediately is that the stack grows *downwards* in memory. When you add something to the top of the stack, it will be inserted at a memory address lower than the previous thing in the stack. In other words, as the stack grows, the memory address of the top of the stack decreases. To prevent confusion, I will not mention that fact unless it is absolutely necessary because we are working with memory addresses of items on the stack.

The `push` instruction will insert some onto the top of the stack, and `pop` will remove data from the top of the stack. For example, `push eax` will allocate more space on the top of the stack and move the value in `eax` to that space, and `pop eax` will move whatever data is at the top of the stack into `eax` and unallocate that space from the stack.

The `esp` register's purpose is to point to the top of the stack. Any data above `esp` is considered not on the stack, it is garbage data. Performing a `push` instruction to add data to the top of the stack (or a `pop` to remove data) will move `esp`. You can also manipulate `esp` directly if you know what you're doing.

The `ebp` register is similar except it always points somewhere in the middle of the current stack frame, directly before the local variables of the current function (we'll talk more about this later). However, calling another function does not move `ebp` automatically, we must do that manually each time.


## The x86 calling convention

x86 has no built-in notion of a function like higher-level languages do. The x86 `call` instruction is essentially just a `jmp` (a `goto`) to another place in memory. In order to use subroutines like we use functions in other languages (which can take arguments and return data back), we must follow a calling convention[^2]. That will also ensure that a subroutine's registers will not be messed up when calling another function.

[^2]: There are multiple calling conventions, but we will be using CDECL, the most popular calling convention for x86 in use by C compilers and assembly programmers.

### Caller rules

Before calling the function, the caller must:

1. Save the *caller-saved registers* by pushing them onto the stack. Some registers are able to be modified by the called function, and to ensure you do not lose the data in those registers, the caller must save them in memory before the call by pushing them onto the stack. These registers are `eax`, `ecx`, and `edx`. If you were not using some or all of those registers then you do not need to save them.
2. Push the function's arguments onto the stack in reverse order (pushing the last argument first and the first argument last). This order ensures that the called function will have its arguments in correct order when popping them from the stack.
3. `call` the subroutine.

[^3]: This is especially important, for example, for C functions with variable number of arguments, since the first argument will be the number of arguments to pop.

The function will store its result in `eax` if applicable. Immediately after the `call`, the caller must:

1. Remove the function's arguments from the stack. This is typically done by simply adding the number of bytes to `esp`. Don't forget that the stack grows downward, so to remove from the stack you must add.
2. Restore the caller-saved registers by popping them from the stack in reverse order. No other registers will have been modified by the called function.

The following example sums up the above caller rules. In this example, assume I have a function called `_subtract` which takes two integer (4-byte) arguments and returns the first argument minus the second argument. In my subroutine called `_mysubroutine`, I call `_subtract` with the arguments `10` and `2`:

```nasm
_mysubroutine:
    ; ...
    ; some code here
    ; ...
    push ecx       ; save the caller-saved registers (I choose to not save eax)
    push edx
    push 2         ; rule 2, push args in reverse order
    push 10
    call _subtract ; eax is now equal to 10-2=8
    add esp, 8     ; remove 8 bytes from the stack (2 arguments, 4 bytes each)
    pop edx        ; restore caller-saved registers
    pop ecx
    ; ...
    ; some code here where I use my amazingly-useful value in eax
    ; ...
```

### Callee rules

In order to be called, a subroutine must:

1. Save the previous frame's base pointer `ebp` by pushing it onto the stack.
2. Adjust `ebp`, which currently points to the previous frame, to point to the current frame (the current value of `esp`).
3. Allocate more space on the stack for local variables, if necessary, by moving the stack pointer `esp`. Since the stack growns downwards, that means you should subtract from `esp`.
4. Save the *callee-saved registers* by pushing them onto the stack. These are: `ebx`, `edi`, and `esi`. You do not have to save any registers you are not planning on modifying.

<figure>
  <img src="/images/2017/beginners-assembly/callee-rules-step1.png">
  <figcaption>
    <p>Fig. 2a: The stack after step 1</p>
  </figcaption>
</figure>

<figure>
  <img src="/images/2017/beginners-assembly/callee-rules-step2.png">
  <figcaption>
    <p>Fig. 2b: The stack after step 2</p>
  </figcaption>
</figure>

<figure>
  <img src="/images/2017/beginners-assembly/callee-rules-step4.png">
  <figcaption>
    <p>Fig. 2c: The stack after step 4</p>
  </figcaption>
</figure>

You may notice a return address in each stack frame in those diagrams. Those are inserted into the stack automatically by `call`. A `ret` instruction pops the address on the top of the stack and jumps to that location. We don't have to use it for anything, I only include it to show why the function's local variables are 4 bytes above `ebp` but the function's arguments are 8 bytes below `ebp`.

You may also notice in the last diagram above that the local variables of a function always begin 4 bytes above `ebp` at the address `ebp-4` (you subtract because addresses go down as you move up the stack) and the arguments of a function always begin 8 bytes below `ebp` at the address `ebp+8` (you add to move down the stack). If you follow the callee rules, this will always be the case for any function.

Once your function is done executing and you wish to return, you should first set `eax` to the return value of your function if necessary. Additionally you must:

1. Restore the callee-saved registers by popping them from the stack in reverse order.
2. Deallocate the space on the stack you allocated in step 3 above for local variables, if applicable. This can be done simply by setting `esp` to `ebp`. This is safe to do even if you didn't allocate any space in the first place.
3. Restore the previous frame's base pointer `ebp` by popping it from the stack.
4. Return with `ret`

Now we'll implement our `_subtract` function from our example above:

```nasm
_subtract:
    push ebp            ; save the previous frame's base pointer
    mov ebp, esp        ; adjust ebp
    ; Here I'd allocate space on the stack for local variables, but I don't need any
    ; Here I'd save the callee-saved registers, but I won't be modifying any
    ; My function begins here
    mov eax, [ebp+8]    ; copy the function's first argument into eax. The brackets mean
                        ; to access the data in memory at the location ebp+8
    sub eax, [ebp+12]   ; subtract the second argument at ebp+12 from the first argument
    ; My function ends here. eax is equal to my function's return value
    ; Here I'd restore the callee-saved registers, but I didn't save any
    ; Here I'd deallocate variables, but I didn't allocate any
    pop ebp             ; restore the previous frame's base pointer
    ret
```

### Enter and Leave

You may notice in the example above that a function will always start the same: `push ebp`, `mov ebp, esp`, and allocating space for local variables. x86 has a handy instruction to accomplish this for us: `enter a b`, where `a` is the number of bytes you'd like to allocate for local variables, and `b` is the "nesting level" which we will always leave at `0`. Additionally, a function always ends with `pop ebp` and `mov esp, ebp`[^3]. This can also be replaced with a single instruction: `leave`. Using these, our example above becomes:

[^3]: While `mov esp, ebp` is only necessary if you've allocated memory on the stack for local variables, as mentioned in point 2 above it is safe to do if you didn't, so `leave` can be used even if you haven't allocated anything.

```nasm
_subtract:
    enter 0, 0          ; save the previous frame's base pointer and adjust ebp
    ; Here I'd save the callee-saved registers, but I won't be modifying any
    ; My function begins here
    mov eax, [ebp+8]    ; copy the function's first argument into eax. The brackets mean
                        ; to access the data in memory at the location ebp+8
    sub eax, [ebp+12]   ; subtract the second argument at ebp+12 from the first argument
    ; My function ends here. eax is equal to my function's return value
    ; Here I'd restore the callee-saved registers, but I didn't save any
    leave               ; deallocate and restore the previous frame's base pointer
    ret
```


## Writing some basic functions

Now that we understand the calling convention, we can begin writing some subroutines. It would be pretty handy to generalizing the code that prints the "Hello world!" to print any string we'd like, a `_print_msg` function.

For that function we will need a `_strlen` function to count the length of the string. That function might look like this in C:

```c
size_t strlen(char *s) {
    size_t length = 0;
    while (*s != 0)
    {           // loop start
        length++;
        s++;
    }           // loop end
    return length;
}
```

In other words, starting at the beginning of the string, we add `1` to the return value for every character we see that is not the string-terminating null character `0`. Once that null character is seen, we return. In assembly it is also pretty simple using our example `_subtract` function above as a base:

```nasm
_strlen:
    enter 0, 0          ; save the previous frame's base pointer and adjust ebp
    ; Here I'd save the callee-saved registers, but I won't be modifying any
    ; My function begins here
    mov eax, 0          ; length = 0
    mov ecx, [ebp+8]    ; copy the function's first argument (pointer to the first
                        ; character of the string) into ecx (which is caller-saved, so
                        ; no need to save it)
_strlen_loop_start:     ; this is a label we can jump to
    cmp byte [ecx], 0   ; dereference that pointer and compare it to null. By default,
                        ; many times a memory access will default to reading 32 bits
                        ; (4 bytes) from memory. Other times it will always be
                        ; required. Here we use a Size Directive to only read one byte,
			; since a character is only one byte
    je _strlen_loop_end ; jump out of the loop if it is equal to null
    inc eax             ; now we're in the loop body. add 1 to our return value
    add ecx, 1          ; increment to the next character in the string
    jmp _strlen_loop_start  ; jump back to the top of the loop
_strlen_loop_end:
    ; My function ends here. eax is equal to my function's return value
    ; Here I'd restore the callee-saved registers, but I didn't save any
    leave               ; deallocate and restore the previous frame's base pointer
    ret
```

That wasn't too bad, right? Writing the code in C beforehand may help you a lot because much of it can be directly converted to assembly. Now we can use this function in our `_print_msg` function, which will require everything we've learned so far:

```nasm
_print_msg:
    enter 0, 0
    ; My function begins here
    mov eax, 0x04       ; 0x04 = the write() syscall
    mov ebx, 0x1        ; 0x1 = standard output
    mov ecx, [ebp+8]    ; the string we want to print is the first arg of this function
    ; at this point we wish to set edx to the length of the string. time to call _strlen
    push eax            ; save the caller-saved registers (I choose to not save edx)
    push ecx       
    push dword [ebp+8]  ; push _strlen's argument, the string argument to _print_msg. NASM
                        ; complains if you do not put a size directive here, and I'm not
                        ; sure why. Anyway, a pointer is a dword (4 bytes, 32 bits)
    call _strlen        ; eax is now equal to the length of the string
    mov edx, eax        ; move the length into edx where we wanted it
    add esp, 4          ; remove 4 bytes from the stack (one 4-byte char* argument)
    pop ecx             ; restore caller-saved registers
    pop eax
    ; we're done calling _strlen and setting up the syscall
    int 0x80
    leave
    ret
```

And lets see the fruit of our hard work by using that function in our complete "Hello world!" program:

```nasm
_start:
    enter 0, 0
    ; save the caller-saved registers (I choose to not save any)
    push hello_world    ; push the argument to _print_msg
    call _print_msg
    mov eax, 0x01           ; 0x01 = exit()
    mov ebx, 0              ; 0 = no errors
    int 0x80
```

That is the end of Part 1. Believe it or not, we have covered all the main x86 topics you will need to write basic x86 programs! In the next article we will apply this knowledge to write our RPN calculator. Now that we have all the introductory material and theory out of the way, Part 2 will be focusing entirely on the code. The functions we write will be much longer and will even have to use some local variables as well.

If you'd like to see the complete program up to this point click [here](https://gist.github.com/gurchik/79dca38ccc2a5e263d0635f1b7737ec9). Thanks for reading! I'll see you in [Part 2](/2017/beginners-assembly-part2/).

## Additional reading

* [University of Virginia's Guide to x86 Assembly](http://www.cs.virginia.edu/~evans/cs216/guides/x86.html) -- Goes more into depth on many of the topics covered here, including more information on each of the most common x86 instructions. A great reference for the most common x86 instructions as well.
* [The Art of Picking Intel Registers](http://www.swansontec.com/sregisters.html) -- While most of the x86 registers are general-purpose, many of the registers have a historical meaning. Following those conventions can improve code readability, and as an interesting side benefit, will even slightly optimize the size of your binaries.
* [NASM: Intel x86 Instruction Reference](http://www.posix.nl/linuxassembly/nasmdochtml/nasmdoca.html) - a full reference to all the obscure x86 instructions.
