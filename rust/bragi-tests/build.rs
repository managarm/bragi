fn main() -> Result<(), Box<dyn std::error::Error>> {
    for test in [
        "arrays", "basic", "empty", "enums", "group", "preamble", "struct", "using",
    ] {
        let path = format!("../../tests/{test}/{test}.bragi");
        let out_path = format!("{test}.rs");

        bragi_build::generate_bindings(path, &out_path)?;
    }

    Ok(())
}
