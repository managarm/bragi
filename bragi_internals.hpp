#include <type_traits>
#include <cstdint>
#include <cstddef>

namespace bragi {

struct varint {
	varint(uint64_t value)
	: value{value} {}

	uint64_t value;

	size_t encode(uint8_t *buf) {
		uint8_t *original_buf = buf;
		int data_bits = 64 - __builtin_clzll(value | 1); // Make sure that we fill at least 1 byte if data == 0
		int bytes = 1 + (data_bits - 1) / 7;

		uint64_t val = this->value;

		if(data_bits > 56){
			*buf++ = 0;
			bytes = 8;
		} else {
			val = ((2 * val + 1) << (bytes - 1));
		}

		for(int i = 0; i < bytes; i++)
			*buf++ = (val >> (i * 8)) & 0xFF;

		return buf - original_buf;
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


struct writer {
	writer(uint8_t *buf, size_t size)
	: _buf{buf}, _size{size} {}

	template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
	size_t serialize(size_t off, T val) {
		for (size_t i = 0; i < sizeof(T); i++) {
			_buf[off + i] = (val & 0xFF);
			val >>= 8;
		}

		return sizeof(T);
	}

	template <typename T, typename = typename T::value_type>
	size_t serialize(size_t off, T val, size_t size) {
		for (size_t i = 0; i < size; i++) {
			serialize<typename T::value_type>(off + i * sizeof(typename T::value_type), val.size() > i ? val[i] : 0);
		}

		return size * sizeof(typename T::value_type);
	}

	template <typename T, typename = std::enable_if_t<std::is_same_v<T, varint>>>
	size_t serialize(size_t off, varint val){
		return val.encode(_buf[off]);
	}

	uint8_t *buf() {
		return _buf;
	}
private:
	uint8_t *_buf;
	size_t _size;
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
