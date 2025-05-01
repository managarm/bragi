pub fn generate_bindings<P>(
    bragi_source_path: P,
    output_file_name: &str,
) -> Result<(), Box<dyn std::error::Error>>
where
    P: AsRef<std::path::Path>,
{
    let out_dir = std::env::var("OUT_DIR")?;
    let out_path = std::path::PathBuf::from(out_dir).join(output_file_name);

    // Invoke the bragi compiler
    let output = std::process::Command::new("bragi")
        .arg("-o")
        .arg(out_path.to_str().unwrap())
        .arg(bragi_source_path.as_ref())
        .arg("rust")
        .output()?;

    if output.status.success() {
        // Make sure the build script is re-run if the source file changes
        println!(
            "cargo::rerun-if-changed={}",
            bragi_source_path.as_ref().display()
        );

        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);

        Err(format!("Bragi compiler failed:\n{stdout}\n{stderr}").into())
    }
}
