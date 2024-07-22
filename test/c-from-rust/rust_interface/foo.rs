// declaration of the function implemented in the C library
extern "C" {
    pub fn c_func(input: i32) -> i32;
}

// wrapper to call the C function
pub fn c_call(i:i32) -> i32{
   unsafe {
    return c_func(i);
    }
}
