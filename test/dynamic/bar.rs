
extern crate baz;
pub fn hello(){
 baz::hello();
 println!("hello bar");
}

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

