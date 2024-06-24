extern crate bar;

#[no_mangle]
pub extern "C" fn foo(x: i32) -> i32 {
    return bar::bar(x);
}
