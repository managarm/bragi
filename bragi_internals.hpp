#include <type_traits>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

namespace bragi {

namespace detail {
	template <typename T>
	inline T bswap(T val) {
		if constexpr (sizeof(T) == 2)
			return __builtin_bswap16(val);
		else if constexpr (sizeof(T) == 4)
			return __builtin_bswap32(val);
		else if constexpr (sizeof(T) == 8)
			return __builtin_bswap64(val);
		else
			return val;
	}

	constexpr inline size_t size_of_varint(uint64_t val) {
		return 8;
		/*int data_bits = 64 - __builtin_clzll(val | 1);
		int bytes = 1 + (data_bits - 1) / 7;

		if(data_bits > 56)
			return 9;

		return bytes;*/
	}
} // namespace detail

struct limited_writer {
	limited_writer(uint8_t *buf, size_t size)
	: buf_{buf}, size_{size} {}

	bool write(size_t offset, const void *data, size_t size) {
		if (offset + size > size_)
			return false;

		memcpy(buf_ + offset, data, size);

		return true;
	}

private:
	uint8_t *buf_;
	size_t size_;
};

struct limited_reader {
	limited_reader(uint8_t *buf, size_t size)
	: buf_{buf}, size_{size} {}

	bool read(size_t offset, void *data, size_t size) {
		if (offset + size > size_)
			return false;

		memcpy(data, buf_ + offset, size);

		return true;
	}

private:
	uint8_t *buf_;
	size_t size_;
};

struct serializer {
	template <typename T, typename Writer>
	bool write_integer(Writer &wr, T val) {
#if __ENDIANNESS__ != __LITTLE_ENDIAN__
		val = detail::bswap(val);
#endif
		return wr.write(advance(sizeof(T)), &val, sizeof(T));
	}

	template <typename Writer>
	bool write_varint(Writer &wr, uint64_t val) {
		return write_integer<uint64_t>(wr, val);
		/*uint8_t buf[9];
		uint8_t *ptr = buf;

		// Make sure that we fill at least 1 byte if data == 0
		int data_bits = 64 - __builtin_clzll(val | 1);
		int bytes = 1 + (data_bits - 1) / 7;

		if(data_bits > 56) {
			*ptr++ = 0;
			bytes = 8;
		} else {
			val = ((2 * val + 1) << (bytes - 1));
		}

		for(int i = 0; i < bytes; i++)
			*ptr++ = (val >> (i * 8)) & 0xFF;

		size_t n = ptr - buf;
		return wr.write(advance(n), buf, n);*/
	}

private:
	size_t index_ = 0;

	size_t advance(size_t n) {
		size_t i = index_;
		index_ += n;
		return i;
	}
};

struct deserializer {
	static constexpr size_t index_stack_size = 2;

	template <typename T, typename Reader>
	bool read_integer(Reader &rd, T &out) {
		T val;

		if (!rd.read(advance(sizeof(T)), &val, sizeof(T)))
			return false;

#if __ENDIANNESS__ != __LITTLE_ENDIAN__
		val = detail::bswap(val);
#endif

		out = val;
		return true;
	}

	template <typename Reader>
	bool read_varint(Reader &rd, uint64_t &out) {
		return read_integer<uint64_t>(rd, out);
		/*uint8_t d[9];

		if (!rd.read(advance(1), d, 1))
			return false;

		int n_bytes = d[0] ? __builtin_ctz(d[0]) + 1 : 9;
		if (n_bytes > 8)
			n_bytes = 9;

		if (n_bytes - 1 && !rd.read(advance(n_bytes - 1), d + 1, n_bytes - 1))
			return false;

		uint64_t ret = 0;
		uint64_t shift = n_bytes < 9 ? 8 - (n_bytes % 8) : 0;

		for(int i = 1; i < n_bytes; i++) {
			ret |= static_cast<uint64_t>(d[i]) << ((i - 1) * 8);
		}

		ret <<= shift;
		ret |= static_cast<uint64_t>(d[0]) >> n_bytes;

		out = ret;
		return true;*/
	}

	void push_index(size_t index) {
		assert((n_index_ + 1) < index_stack_size);
		index_stack_[++n_index_] = index;
	}

	void pop_index() {
		n_index_--;
	}

private:
	size_t index_stack_[index_stack_size]{};
	size_t n_index_ = 0;

	size_t advance(size_t n) {
		assert(n);
		size_t i = index_stack_[n_index_];
		index_stack_[n_index_] += n;
		return i;
	}
};

} // namespace bragi
