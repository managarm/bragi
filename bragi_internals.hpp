#include <type_traits>
#include <cstdint>
#include <cstddef>

namespace bragi {

struct varint {
	template <typename F>
	static bool write(uint64_t value, F func) {
		// Make sure that we fill at least 1 byte if data == 0
		int data_bits = 64 - __builtin_clzll(value | 1);
		int bytes = 1 + (data_bits - 1) / 7;

		uint64_t val = this->value;

		if(data_bits > 56){
			if (!func(0))
				return false;
			bytes = 8;
		} else {
			val = ((2 * val + 1) << (bytes - 1));
		}

		for(int i = 0; i < bytes; i++)
			if (!func((val >> (i * 8)) & 0xFF))
				return false;

		return true;
	}

	size_t decode(uint8_t *data) {
		int n_bytes = data[0] ? __builtin_ctz(data[0]) + 1 : 9;
		if (n_bytes > 8)
			n_bytes = 9;

		uint64_t ret = 0;
		uint64_t shift = n_bytes < 9 ? 8 - (n_bytes % 8) : 0;

		for(int i = 1; i < n_bytes; i++) {
			ret |= static_cast<uint64_t>(data[i]) << ((i - 1) * 8);
		}

		ret <<= shift;
		ret |= static_cast<uint64_t>(data[0]) >> n_bytes;

		this->value = ret;

		return n_bytes;
	}
};

struct limited_writer {
	limited-writer(uint8_t *buf, size_t size)
	: buf_{buf}, size_{size} {}

	template <typename T>
	bool write_integer(T val) {
		for (size_t i = 0; i < sizeof(T); i++) {
			buf_[index_++] = (val & 0xFF);
			val >>= 8;

			if (index_ >= size_)
				return false;
		}

		return true;
	}

	template <typename T>
	bool write_integer_at(size_t pos, T val) {
		for (size_t i = 0; i < sizeof(T); i++) {
			if (pos + i >= size_)
				return false;
			buf_[pos + i] = (val & 0xFF);
			val >>= 8;
		}

		return true;
	}

	template <typename T>
	bool write_integer_array(const T *val, size_t data_size, size_t total_size) {
		for (size_t i = 0; i < total_size; i++) {
			if (!write_integer<T>(data_size > i ? val[i] : 0))
				return false;
		}

		return true;
	}

	size_t write_varint(uint64_t val) {
		return varint::write(val, [&] (uint8_t v) {
			buf_[index_++] = v;
			return index_ < size_;
		});
	}

	uint8_t *buf() const {
		return buf_;
	}

	size_t index() {
		return index_;
	}

private:
	uint8_t *buf_;
	size_t size_;
	size_t index_;
};

struct reader {
	reader(uint8_t *buf, size_t size)
	: _buf{buf}, _size{size} {}

	template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
	T deserialize(size_t off) {
		std::make_unsigned_t<T> val = 0;
		for (size_t i = 0; i < sizeof(T); i++) {
			val |= static_cast<std::make_unsigned_t<T>>(_buf[off + i]) << (i * 8);
		}

		return val;
	}

	template <typename T, typename = typename T::value_type>
	T deserialize(size_t off, size_t size) {
		T val{};
		for (size_t i = 0; i < size; i++) {
			auto v = deserialize<typename T::value_type>(off + i * sizeof(typename T::value_type));
			val.push_back(v);
		}

		return val;
	}

	template <typename T, typename = std::enable_if_t<std::is_same_v<T, varint>>>
	T deserialize(size_t off, size_t &out_size){
		varint ret{};
		out_size = ret.decode(_buf[off]);
		return ret.value;
	}

private:
	uint8_t *_buf;
	size_t _size;
};

} // namespace bragi
