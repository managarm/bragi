# bragi-build

This crate provides a helper function for invoking the
[bragi](https://github.com/managarm/bragi) code generator from
within a `build.rs` file.

## Usage

Simply call the `bragi_build::generate_bindings` function with two arguments:
the bragi source file path and the output file name.

The generated bindings will be written to the output directory under the specified
name and a cargo instruction will be printed out to make sure the build script
is re-run if the bragi source file is modified.

## License

This crate is licensed under the MIT license.
See the [LICENSE](LICENSE) file for more details.
