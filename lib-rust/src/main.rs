mod quotes;
use quotes::replace_quotes;
// mod test;

fn main() {
    let code = r#"
"abcdef"
a = "b"
    "#;
    let replaced = replace_quotes(code);
    print!("{}", replaced);

    // test::test();
}
