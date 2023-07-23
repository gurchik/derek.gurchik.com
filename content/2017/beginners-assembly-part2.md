---
template: "post.html.j2"
title: "A Beginner's Guide to x86 Assembly, Part 2 of 2"
date: 2017-02-13
summary: "In the final part of this series we will use our new knowledge to implement the calculator from the ground up."
---

In the [previous part of this series](/2017/beginners-assembly-part1) the main topics of x86 assembly programming such as the call stack x86 calling convention were introduced. In this final part we will apply that knowledge to write our RPN calculator.

The complete code of our calculator can be found [here](https://gist.github.com/gurchik/9dff75a67710207e16cd6a8531393ccf). It is heavily commented and may serve as a sufficient learning resource for those of you with some knowledge of assembly already. Now, lets get started.

For those of you unfamiliar with Reverse Polish notation (sometimes called postfix notation), expressions are evaluated using a stack. Therefore, we'll need to create a stack to use as well as some `_pop` and `_push` functions to manipulate that stack. We'll also need a function called `_print_answer` which will print the string-representation of the numeric result at the end of our calculation.


## Creating the stack

First we'll define a space in memory we will use for our stack as well as our global `stack_size` variable. We will wish to modify these variables so they will not go in the `.rodata` section, but instead, `.data`:

```nasm
section .data
    stack_size: dd 0        ; create a dword (4-byte) variable set to zero
    stack: times 256 dd 0   ; fill the stack with 256 dword zeroes 
```

Then we can implement the functions `_push` and `_pop`:

```nasm
_push:
    enter 0, 0
    ; Save the callee-saved registers that I'll be using
    push eax
    push edx
    mov eax, [stack_size]
    mov edx, [ebp+8]
    mov [stack + 4*eax], edx    ; Insert the arg into the stack. We scale
                                ; by 4 because each dword is 4 bytes each
    inc dword [stack_size]      ; Add 1 to stack_size
    ; Restore the callee-saved registers we used
    pop edx
    pop eax
    leave
    ret

_pop:
    enter 0, 0
    ; Save the callee-saved registers
    dec dword [stack_size]      ; Subtract 1 from stack_size first
    mov eax, [stack_size]
    mov eax, [stack + 4*eax]    ; Set the number at the top of the stack to eax
    ; Here I'd restore the callee-saved registers, but I didn't save any
    leave
    ret
```


## Printing numbers

`_print_answer` is a lot more complicated because we will have to convert numbers to strings, and that process requires using a few other functions. We'll need a `_putc` function which will print a single character, a `mod` function to calculate the modulus of two arguments, and `_pow_10` to calculate a power of 10. You'll see why we need them later. These are pretty simple so lets do that now:

```nasm
_pow_10:
    enter 0, 0
    mov ecx, [ebp+8]    ; set ecx (caller-saved) to function arg
    mov eax, 1          ; first power of 10 (10**0 = 1)
_pow_10_loop_start:     ; multiply eax by 10 until ecx is 0
    cmp ecx, 0
    je _pow_10_loop_end
    imul eax, 10
    sub ecx, 1
    jmp _pow_10_loop_start
_pow_10_loop_end:
    leave
    ret

_mod:
    enter 0, 0
    push ebx
    mov edx, 0          ; explained below
    mov eax, [ebp+8]
    mov ebx, [ebp+12]
    idiv ebx            ; divides the 64-bit integer [edx:eax] by ebx. We only want to
                        ; divide the 32-bit integer eax, so we set edx to zero. The
                        ; result of this division is stored in eax, and the remainder
                        ; is stored in edx. As always, you can find more about this
                        ; instruction in the resources below.
    mov eax, edx        ; return the modulus
    pop ebx
    leave
    ret

_putc:
    enter 0, 0
    mov eax, 0x04       ; write()
    mov ebx, 1          ; standard out
    lea ecx, [ebp+8]    ; the input character
    mov edx, 1          ; print only 1 character
    int 0x80
    leave
    ret
```

Now, how do we print the digits of a number? First, note that we can get the last digit of a number by finding the modulus of `10` (for example, `123 % 10 = 3`), and we can get the next digit by finding the modulus of `100` and dividing that result by `10` (for example, `(123 % 100)/10 = 2`). In general, we can find a specific digit (going from right to left) of a number by finding `(number % 10**n) / 10**(n-1)`, where the ones digit would be `n = 1`, the tens digit `n = 2` and so on.

Using that knowledge we can find all the digits of a number by starting at `n = 1` and iterating to `n = 10` (the most digits a signed 4-byte integer can have). However, it would be a lot easier if we could go from left to right -- that would allow us to print each character as we find it and prevent trailing zeroes to the left of the number -- so we'll instead iterate from `n = 10` to `n = 1`.

It should look something like the following C code:

```c
#define MAX_DIGITS 10
void print_answer(int a) {
    if (a < 0) { // if the number is negative
        putc('-'); // print a negative sign
        a = -a; // convert the number to positive
    }
    int started = 0;
    for (int i = MAX_DIGITS; i > 0; i--) {
        int digit = (a % pow_10(i)) / pow_10(i-1);
        if (digit == 0 && started == 0) continue; // don't print trailing zeroes
        started = 1;
        putc(digit + '0');
    }
}
```

Now you'll see why we need those three functions we implemented before. Now lets implement this in assembly:

```nasm
%define MAX_DIGITS 10

_print_answer:
    enter 1, 0              ; we'll use 1 byte for "started" variable in C
    push ebx
    push edi
    push esi
    mov eax, [ebp+8]        ; our "a" argument
    cmp eax, 0              ; if the number is not negative, skip this if-statement
    jge _print_answer_negate_end
    ; call putc for '-'
    push eax
    push 0x2d               ; '-' character
    call _putc
    add esp, 4
    pop eax
    neg eax                 ; convert a to positive
_print_answer_negate_end:
    mov byte [ebp-4], 0     ; started = 0
    mov ecx, MAX_DIGITS     ; our i variable
_print_answer_loop_start:
    cmp ecx, 0
    je _print_answer_loop_end
    ; call pow_10 for ecx. We'll be trying to get ebx to be out "digit" variable in C.
    ; For now we'll get edx = pow_10(i-1) and ebx = pow_10(i)
    push eax
    push ecx
    dec ecx             ; i-1
    push ecx            ; arg1 for _pow_10
    call _pow_10
    mov edx, eax        ; edx = pow_10(i-1)
    add esp, 4
    pop ecx             ; restore ecx to i
    pop eax
    ; end pow_10 call
    mov ebx, edx        ; digit = ebx = pow_10(i-1)
    imul ebx, 10        ; digit = ebx = pow_10(i)
    ; call _mod for (a % pow_10(i)), which is (eax mod ebx)
    push eax
    push ecx
    push edx
    push ebx            ; arg2, ebx = digit = pow_10(i)
    push eax            ; arg1, eax = a
    call _mod
    mov ebx, eax        ; digit = ebx = a % pow_10(i+1), almost there
    add esp, 8
    pop edx
    pop ecx
    pop eax
    ; end mod call
    ; divide ebx ("digit" var) by pow_10(i) (edx).  We'll need to save a few registers
    ; since idiv requires both edx and eax for the dividend. Since edx is our divisor,
    ; we'll need to move it to some other register
    push esi
    mov esi, edx
    push eax
    mov eax, ebx
    mov edx, 0
    idiv esi            ; eax holds the result (the digit)
    mov ebx, eax        ; ebx = (a % pow_10(i)) / pow_10(i-1), the "digit" variable in C
    pop eax
    pop esi
    ; end division
    cmp ebx, 0                        ; if digit == 0
    jne _print_answer_trailing_zeroes_check_end
    cmp byte [ebp-4], 0               ; if started == 0
    jne _print_answer_trailing_zeroes_check_end
    jmp _print_answer_loop_continue   ; continue
_print_answer_trailing_zeroes_check_end:
    mov byte [ebp-4], 1     ; started = 1
    add ebx, 0x30           ; digit + '0'
    ; call putc
    push eax
    push ecx
    push edx
    push ebx
    call _putc
    add esp, 4
    pop edx
    pop ecx
    pop eax
    ; end call putc
_print_answer_loop_continue:
    sub ecx, 1
    jmp _print_answer_loop_start
_print_answer_loop_end:
    pop esi
    pop edi
    pop ebx
    leave
    ret
```

That was a tough one! Hopefully tracing through the comments help. If now all you're thinking is "Man I sure wish I could have used `printf("%d")`, then you will enjoy the end of this article when we replace this function with just that! 

Now that we have all the functions necessary, we can implement the main logic in `_start` and we'll be done!


## Evaluating Reverse Polish notation

As we've said before, Reverse Polish notation is evaluated using a stack. When a number is read it is pushed onto the stack, and when an operator is read it is applied to the two operands at the top of the stack.

For example, if we wish to evaluate `84/3+6*`[^1], that process would look like:

| Step | Character checked | Stack before  | Stack after  |
|:----:|:-----------------:|:-------------:|:------------:|
|   1  |      `8`          | `[]`          | `[8]`        |
|   2  |      `4`          | `[8]`         | `[8, 4]`     |
|   3  |      `/`          | `[8, 4]`      | `[2]`        |
|   4  |      `3`          | `[2]`         | `[2, 3]`     |
|   5  |      `+`          | `[2, 3]`      | `[5]`        |
|   6  |      `6`          | `[5]`         | `[5, 6]`     |
|   7  |      `*`          | `[5, 6]`      | `[30]`       |

[^1]: `6384/+*` is another way of writing the same expression.

If the input is a valid postfix expression, at the end there will only be one element on the stack, which will be the answer the expression evaluates to. So in this case, the expression evaluates to `30`.

What we need to implement in assembly is something like the following C code:

```c
int stack[256];         // 256 is probably plenty big for our stack
int stack_size = 0;

int main(int argc, char *argv[]) {
    char *input = argv[0];
    size_t input_length = strlen(input);
    
    for (int i = 0; i < input_length; i++) {
        char c = input[i];
        if (c >= '0' && c <= '9') { // if the character is a digit
            push(c - '0'); // convert the character digit to an integer and push that
        } else {
            int b = pop();
            int a = pop();
            if (c == '+') {
                push(a+b);
            } else if (c == '-') {
                push(a-b);
            } else if (c == '*') {
                push(a*b);
            } else if (c == '/') {
                push(a/b);
            } else {
                error("Invalid input\n");
                exit(1);
            }
        }
    }
    
    if (stack_size != 1) {
        error("Invalid input\n");
        exit(1);
    }
    
    print_answer(stack[0]);
    exit(0);
}
```

Since we now have all of the functions necessary to implement this, lets get started.

```nasm
_start:
    ; you do not get the arguments of _start the same way you do in other functions.
    ; instead, esp points directly to argc (the number of arguments), and esp+4 points
    ; to argv. Therefore, esp+4 points to the name of your program, esp+8 points to
    ; the first argument, etc
    mov esi, [esp+8]         ; esi = "input" = argv[0]
    ; call _strlen to find the length of the input
    push esi
    call _strlen
    mov ebx, eax             ; ebx = input_length
    add esp, 4
    ; end _strlen call
    mov ecx, 0               ; ecx = "i"
_main_loop_start:
    cmp ecx, ebx             ; if (i >= input_length)
    jge _main_loop_end
    mov edx, 0
    mov dl, [esi + ecx]      ; load only a byte from memory into the lower byte of
                             ; edx. We set the rest of edx to zero.
                             ; edx = c variable = input[i]
    cmp edx, '0'
    jl _check_operator
    cmp edx, '9'
    jg _print_error
    sub edx, '0'
    mov eax, edx             ; eax = c variable - '0' (the numeric digit, not char)
    jmp _push_eax_and_continue
_check_operator:
    ; call _pop twice to pop b into edi and a into eax
    push ecx
    push ebx
    call _pop
    mov edi, eax             ; edi = b
    call _pop                ; eax = a
    pop ebx
    pop ecx
    ; end call _pop
    cmp edx, '+'
    jne _subtract
    add eax, edi                 ; eax = a+b
    jmp _push_eax_and_continue
_subtract:
    cmp edx, '-'
    jne _multiply
    sub eax, edi                 ; eax = a-b
    jmp _push_eax_and_continue
_multiply:
    cmp edx, '*'
    jne _divide
    imul eax, edi                ; eax = a*b
    jmp _push_eax_and_continue
_divide:
    cmp edx, '/'
    jne _print_error
    push edx                     ; save edx since we'll need to set it to 0 for idiv
    mov edx, 0
    idiv edi                     ; eax = a/b
    pop edx
    ; now we push eax and continue
_push_eax_and_continue:
    ; call _push
    push eax
    push ecx
    push edx
    push eax          ; arg1
    call _push
    add esp, 4
    pop edx
    pop ecx
    pop eax
    ; end call _push
    inc ecx
    jmp _main_loop_start
_main_loop_end:
    cmp byte [stack_size], 1      ; if (stack_size != 1) print error
    jne _print_error
    mov eax, [stack]
    push eax
    call _print_answer
    ; print a final newline
    push 0xA
    call _putc
    ; exit successfully
    mov eax, 0x01           ; 0x01 = exit()
    mov ebx, 0              ; 0 = no errors
    int 0x80                ; execution will end here
_print_error:
    push error_msg
    call _print_msg
    mov eax, 0x01
    mov ebx, 1
    int 0x80
```

You'll also need to add a `error_msg` string to your `.rodata` section, something like:

```nasm
section .rodata
    ; Declare some bytes at a symbol called error_msg. NASM's db pseudo-instruction
    ; allows either a single byte value, a constant string, or a combination of the two
    ; as seen here. 0xA = new line, and 0x0 = string-terminating null
    error_msg: db "Invalid input", 0xA, 0x0
```

And we're done! Time to impress all your friends, if you have any. Hopefully at this point you have a new appreciation for higher-level languages, especially when you realize that many older programs were written entirely or almost entirely in assembly, such as the original RollerCoaster Tycoon!

The complete code can be found [here](https://gist.github.com/gurchik/9dff75a67710207e16cd6a8531393ccf). Thanks for reading! Continue on for some extra credit, if you dare.


## Next steps

Here are some features you can add for additional practice:

1. Throw an error if the user does not supply 1 argument to the program instead of just segfaulting
2. Add support for optional spaces between operands and operators in the input
3. Add support for multi-digit operands
4. Allow negative numbers in the input
5. Replace `_strlen` with the one in [the C standard library](https://en.wikipedia.org/wiki/X86_assembly_language#.22Hello_world.21.22_program_for_Linux_in_NASM_style_assembly_using_the_C_standard_library) and `_print_answer` with a call to `printf`.


## Additional reading

* [University of Virginia's Guide to x86 Assembly](http://www.cs.virginia.edu/~evans/cs216/guides/x86.html) -- Goes more into depth on many of the topics covered here, including more information on each of the most common x86 instructions. A great reference for the most common x86 instructions as well.
* [The Art of Picking Intel Registers](http://www.swansontec.com/sregisters.html) -- While most of the x86 registers are general-purpose, many of the registers have a historical meaning. Following those conventions can improve code readability, and as an interesting side benefit, will even slightly optimize the size of your binaries.
* [NASM: Intel x86 Instruction Reference](http://www.posix.nl/linuxassembly/nasmdochtml/nasmdoca.html) - a full reference to all the obscure x86 instructions.
