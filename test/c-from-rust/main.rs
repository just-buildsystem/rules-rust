use std::env;

extern crate foo_rust;

fn main() {
   let args: Vec<String> = env::args().collect();
   match args[1].parse::<i32>() {
	 Ok(i) =>  println!("Absolute value of {} is {}", i, foo_rust::c_call(i)),
	 Err(..) => println!("Wrong argument {}",args[1]),
	 };
    
}
