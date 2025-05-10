use std::io::{Cursor, Read, Result, Seek, SeekFrom, Write};

#[doc(hidden)]
pub use array_init::array_init;

#[doc(hidden)]
pub trait Primitive: Sized {
    fn write<W: Write>(self, writer: &mut Writer<W>) -> Result<()>;
    fn read<R: Read + Seek>(reader: &mut Reader<R>) -> Result<Self>;
}

macro_rules! impl_primitive {
    ($($ty:ty),*) => {
        $(impl Primitive for $ty {
            fn write<W: Write>(self, writer: &mut Writer<W>) -> Result<()> {
                let bytes = self.to_le_bytes();
                writer.write_all(&bytes)
            }

            fn read<R: Read + Seek>(reader: &mut Reader<R>) -> Result<Self> {
                let mut bytes = [0; std::mem::size_of::<$ty>()];
                reader.read_exact(&mut bytes)?;
                Ok(Self::from_le_bytes(bytes))
            }
        })*
    };
}

impl_primitive!(u8, u16, u32, u64, usize, i8, i16, i32, i64, isize);

#[doc(hidden)]
pub struct Writer<'a, W: Write> {
    writer: &'a mut W,
    offset: usize,
}

#[doc(hidden)]
pub struct Reader<'a, R: Read + Seek> {
    reader: &'a mut R,
}

impl<'a, W: Write> Writer<'a, W> {
    pub fn new(writer: &'a mut W) -> Self {
        Self { writer, offset: 0 }
    }

    pub fn offset(&self) -> usize {
        self.offset
    }

    pub fn write_all(&mut self, buf: &[u8]) -> Result<()> {
        self.writer.write_all(buf)?;
        self.offset += buf.len();
        Ok(())
    }

    pub fn write_integer<T: Primitive>(&mut self, value: T) -> Result<()> {
        value.write(self)
    }

    pub fn write_string(&mut self, value: &str) -> Result<()> {
        let bytes = value.as_bytes();
        self.write_varint(bytes.len() as u64)?;
        self.writer.write_all(bytes)?;
        Ok(())
    }

    pub fn write_varint(&mut self, mut value: u64) -> Result<()> {
        let mut buffer = [0u8; 9];
        let mut length = 0;

        let data_bits = 64 - (value | 1).leading_zeros();
        let mut bytes = 1 + (data_bits.saturating_sub(1) / 7) as usize;

        if data_bits > 56 {
            buffer[length] = 0;
            length += 1;
            bytes = 8;
        } else {
            value = (2 * value + 1) << (bytes - 1);
        }

        for i in 0..bytes {
            buffer[length] = ((value >> (i * 8)) & 0xFF) as u8;
            length += 1;
        }

        self.writer.write_all(&buffer[..length])
    }

    pub fn write_struct<S: Struct>(&mut self, value: &S) -> Result<()> {
        value.encode_body(self.writer)
    }
}

impl<'a, R: Read + Seek> Reader<'a, R> {
    pub fn new(reader: &'a mut R) -> Self {
        Self { reader }
    }

    pub fn offset(&mut self) -> Result<u64> {
        self.reader.stream_position()
    }

    pub fn seek(&mut self, offset: u64) -> Result<u64> {
        self.reader.seek(SeekFrom::Start(offset))
    }

    pub fn read_exact(&mut self, buf: &mut [u8]) -> Result<()> {
        self.reader.read_exact(buf)
    }

    pub fn read_integer<T: Primitive>(&mut self) -> Result<T> {
        T::read(self)
    }

    pub fn read_string(&mut self) -> Result<String> {
        let length = self.read_varint()? as usize;
        let mut buffer = vec![0u8; length];

        self.reader.read_exact(&mut buffer)?;

        match String::from_utf8(buffer) {
            Ok(string) => Ok(string),
            Err(_) => Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Invalid UTF-8 string",
            )),
        }
    }

    pub fn read_varint(&mut self) -> Result<u64> {
        let mut bytes = [0u8; 9];

        self.reader.read_exact(&mut bytes[..1])?;

        let mut n_bytes = if bytes[0] != 0 {
            bytes[0].trailing_zeros() as usize + 1
        } else {
            9
        };

        if n_bytes > 8 {
            n_bytes = 9;
        }

        if n_bytes > 1 {
            self.reader.read_exact(&mut bytes[1..n_bytes])?;
        }

        let mut value: u64 = 0;
        let shift = if n_bytes < 9 { 8 - (n_bytes % 8) } else { 0 };

        for (i, byte) in bytes.iter().enumerate().skip(1) {
            value |= (*byte as u64) << ((i - 1) * 8);
        }

        value <<= shift;
        value |= (bytes[0] as u64) >> n_bytes;

        Ok(value)
    }

    pub fn read_struct<S: Struct>(&mut self, value: &mut S) -> Result<()> {
        value.decode_body(self.reader)
    }
}

#[doc(hidden)]
pub trait Struct {
    fn size_of_body(&self) -> usize;

    fn encode_body<W: Write>(&self, writer: &mut W) -> Result<()>;
    fn decode_body<R: Read + Seek>(&mut self, reader: &mut R) -> Result<()>;
}

#[doc(hidden)]
pub trait Message {
    const MESSAGE_ID: u32;
    const HEAD_SIZE: usize;

    fn size_of_head(&self) -> usize;
    fn size_of_tail(&self) -> usize;

    fn encode_head<W: Write>(&self, writer: &mut W) -> Result<()>;
    fn encode_tail<W: Write>(&self, writer: &mut W) -> Result<()>;

    fn decode_head<R: Read + Seek>(&mut self, reader: &mut R) -> Result<()>;
    fn decode_tail<R: Read + Seek>(&mut self, reader: &mut R) -> Result<()>;
}

/// The preamble of a message. It consists of the message ID
/// and the size of the encoded tail of the message.
#[derive(Debug, Clone, Copy)]
pub struct Preamble {
    id: u32,
    tail_size: u32,
}

impl Preamble {
    /// Creates a new [`Preamble`] with the given message ID and tail size.
    pub const fn new(id: u32, tail_size: u32) -> Self {
        Self { id, tail_size }
    }

    /// Returns the message ID of the message.
    pub const fn id(&self) -> u32 {
        self.id
    }

    /// Returns the size of the tail of the message.
    pub const fn tail_size(&self) -> u32 {
        self.tail_size
    }
}

#[doc(hidden)]
pub fn size_of_varint(value: u64) -> usize {
    let leading_zeroes = (value | 1).leading_zeros() as usize;
    let data_bits = u64::BITS as usize - leading_zeroes;
    let bytes = 1 + (data_bits - 1) / 7;

    if data_bits > 56 { 9 } else { bytes }
}

/// Reads the preamble of a message from the given reader.
pub fn read_preamble<R: Read + Seek>(reader: &mut R) -> Result<Preamble> {
    let mut preamble = Preamble {
        id: 0,
        tail_size: 0,
    };

    let offset = reader.stream_position()?;

    {
        let mut reader = Reader::new(reader);

        preamble.id = reader.read_integer::<u32>()?;
        preamble.tail_size = reader.read_integer::<u32>()?;
    }

    reader.seek(SeekFrom::Start(offset))?;

    Ok(preamble)
}

/// Writes the preamble of a message to the given writer.
pub fn write_preamble<W: Write>(writer: &mut W, preamble: Preamble) -> Result<()> {
    let mut writer = Writer::new(writer);

    writer.write_integer(preamble.id())?;
    writer.write_integer(preamble.tail_size())?;

    Ok(())
}

/// Reads the message head and tail from the given readers and returns the final message.
/// The message is default initialized before decoding the head and tail.
pub fn read_head_tail<M: Default + Message, H: Read + Seek, T: Read + Seek>(
    head_reader: &mut H,
    tail_reader: &mut T,
) -> Result<M> {
    let mut message = M::default();

    message.decode_head(head_reader)?;
    message.decode_tail(tail_reader)?;

    Ok(message)
}

/// Reads only the message head from the given reader and returns the final message.
/// The message is default initialized before decoding the head.
pub fn read_head_only<M: Default + Message, H: Read + Seek>(head_reader: &mut H) -> Result<M> {
    let mut message = M::default();

    message.decode_head(head_reader)?;

    Ok(message)
}

/// Writes the message head and tail and returns the final head and tail buffers.
/// The head and tail buffers are returned as a tuple of byte vectors.
pub fn write_head_tail<M: Message>(message: &M) -> Result<(Vec<u8>, Vec<u8>)> {
    let mut head_cursor = Cursor::new(vec![0; message.size_of_head()]);
    let mut tail_cursor = Cursor::new(vec![0; message.size_of_tail()]);

    message.encode_head(&mut head_cursor)?;
    message.encode_tail(&mut tail_cursor)?;

    Ok((head_cursor.into_inner(), tail_cursor.into_inner()))
}

/// Writes only the message head and returns the final buffer.
/// The buffer is returned as a byte vector.
pub fn write_head_only<M: Message>(message: &M) -> Result<Vec<u8>> {
    let mut head_cursor = Cursor::new(vec![0; message.size_of_head()]);

    message.encode_head(&mut head_cursor)?;

    Ok(head_cursor.into_inner())
}

#[macro_export]
#[doc(hidden)]
macro_rules! generate_enum {
    (
        $vis:vis enum $name:ident : $underlying:ty {
            $(
                $variant:ident = $value:expr
            ),*
            $(,)?
        }
    ) => {
        #[repr($underlying)]
        #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
        $vis enum $name {
            $(
                $variant = $value,
            )*
        }

        impl ::core::convert::TryFrom<$underlying> for $name {
            type Error = $underlying;

            fn try_from(value: $underlying) -> ::core::result::Result<Self, Self::Error> {
                match value {
                    $(
                        $value => Ok($name::$variant),
                    )*
                    _ => Err(value),
                }
            }
        }
    }
}

#[macro_export]
#[doc(hidden)]
macro_rules! generate_consts {
    (
        $vis:vis enum $name:ident : $underlying:ty {
            $(
                $variant:ident = $value:expr
            ),*
            $(,)?
        }
    ) => {
        #[repr(transparent)]
        #[derive(Debug, Default, Clone, Copy, PartialEq, Eq, Hash)]
        $vis struct $name($underlying);

        impl $name {
            $(
                pub const $variant: Self = Self($value);
            )*

            /// Returns the underlying value of the constant.
            pub const fn value(&self) -> $underlying {
                self.0
            }
        }

        impl ::core::convert::From<$underlying> for $name {
            fn from(value: $underlying) -> Self {
                Self(value)
            }
        }
    }
}

#[macro_export]
#[doc(hidden)]
macro_rules! generate_bitfield_enum {
    (
        $vis:vis enum $name:ident : $underlying:ty {
            $(
                $variant:ident = $value:expr
            ),*
            $(,)?
        }
    ) => {
        #[repr(transparent)]
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        $vis struct $name {
            bits: $underlying,
        }

        impl $name {
            $(
                pub const $variant: Self = Self { bits: $value };
            )*

            #[doc = concat!("Creates a new [`", stringify!($name), "`] with no bits set.")]
            pub const fn empty() -> Self {
                Self { bits: 0 }
            }

            #[doc = concat!("Creates a new [`", stringify!($name), "`] with the given bits set.")]
            #[doc = "# Safety"]
            #[doc = "This function is unsafe because it allows creating a bitfield with arbitrary bits set."]
            #[doc = "The caller must ensure that the bits are valid for the given bitfield."]
            pub const unsafe fn new(bits: u32) -> Self {
                Self { bits }
            }

            #[doc = concat!("Returns the bits of the [`", stringify!($name), "`].")]
            pub const fn bits(&self) -> u32 {
                self.bits
            }

            #[doc = concat!("Checks if the given bits are set in the [`", stringify!($name), "`].")]
            pub const fn is_set(&self, other: Self) -> bool {
                (self.bits & other.bits) == other.bits
            }

            #[doc = concat!("Returns a new [`", stringify!($name), "`] with the given bits set.")]
            pub const fn set(&self, other: Self) -> Self {
                Self { bits: self.bits | other.bits }
            }

            #[doc = concat!("Returns a new [`", stringify!($name), "`] with the given bits cleared.")]
            pub const fn clear(&self, other: Self) -> Self {
                Self { bits: self.bits & !other.bits }
            }
        }

        impl ::core::ops::BitAnd for $name {
            type Output = Self;

            fn bitand(self, rhs: Self) -> Self::Output {
                Self { bits: self.bits & rhs.bits }
            }
        }

        impl ::core::ops::BitOr for $name {
            type Output = Self;

            fn bitor(self, rhs: Self) -> Self::Output {
                Self { bits: self.bits | rhs.bits }
            }
        }

        impl ::core::ops::BitXor for $name {
            type Output = Self;

            fn bitxor(self, rhs: Self) -> Self::Output {
                Self { bits: self.bits ^ rhs.bits }
            }
        }

        impl ::core::ops::Not for $name {
            type Output = Self;

            fn not(self) -> Self::Output {
                Self { bits: !self.bits }
            }
        }

        impl ::core::fmt::Display for $name {
            fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::fmt::Result {
                let mut first = true;
                for (bits, name) in [
                    $(
                        (Self::$variant, stringify!($variant))
                    ),*
                ] {
                    if self.is_set(bits) {
                        if !first {
                            write!(f, " | ")?;
                        }
                        write!(f, "{}", name)?;
                        first = false;
                    }
                }
                if first {
                    write!(f, "NONE")?;
                }
                Ok(())
            }
        }
    };
}

/// A macro to include generated bindings from the `OUT_DIR`.
///
/// The module declared by this macro will contain the generated bindings
/// and will be annotated with attributes to suppress warnings and lints.
#[macro_export]
macro_rules! include_binding {
    ($($vis:vis mod $mod_name:ident = $name:literal),* $(,)?) => {
        $(
            #[allow(clippy::all)]
            #[allow(dead_code)]
            #[allow(unused_imports)]
            #[allow(unused_mut)]
            #[allow(unused_variables)]
            $vis mod $mod_name {
                include!(concat!(env!("OUT_DIR"), "/", $name));
            }
        )*
    };
}
