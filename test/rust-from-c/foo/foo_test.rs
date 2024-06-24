extern crate foo;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_foo(){
       assert_eq!(foo::foo(-7),7);
    }
}