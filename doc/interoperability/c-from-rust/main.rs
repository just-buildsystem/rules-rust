use std::env;

// declaration of the function implemented in the C library
extern "C" {
    fn c_func(input: i32) -> i32;
}

// wrapper to call the C function
fn c_call(i: i32) -> i32 {
    unsafe {
        return c_func(i);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args[1].parse::<i32>() {
        Ok(i) => println!("Absolute value of {} is {}", i, c_call(i)),
        Err(..) => println!("Wrong argument {}", args[1]),
    };
}
