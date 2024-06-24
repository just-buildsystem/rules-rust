
#[cfg(not(bar))]
pub fn hello(){
 println!("hello bar");
}

#[cfg(bar)]
pub fn hello(){
 println!("hello build script");
}

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

