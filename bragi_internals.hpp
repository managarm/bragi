#include <type_traits>
#include <cstdint>

namespace bragi::internals {

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

private:
	uint8_t *_buf;
	size_t _size;
};

} // namespace bragi::internals
