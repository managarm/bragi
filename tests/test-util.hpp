#pragma once

#include <bragi/helpers-all.hpp>
#include <utility>
#include <vector>

#ifdef TEST_FRIGG
#include <bragi/helpers-frigg.hpp>
#include <frg/std_compat.hpp>
#include <frg/vector.hpp>
#include <frg/string.hpp>
#else
#include <bragi/helpers-std.hpp>
#include <string>
#endif

namespace test {

#ifdef TEST_FRIGG

template <typename T>
using vec_of = frg::vector<T, frg::stl_allocator>;

#else

template <typename T>
using vec_of = std::vector<T>;

#endif

template <typename T, typename ...Ts>
auto make_vector(Ts ...ts) {
#ifdef TEST_FRIGG
	frg::vector<T, frg::stl_allocator> vec{frg::stl_allocator{}};

	(vec.push_back(static_cast<T>(ts)), ...);

	return vec;
#else
	return std::vector<T>{static_cast<T>(ts)...};
#endif
}

auto make_string(const char *str) {
#ifdef TEST_FRIGG
	return frg::string<frg::stl_allocator>{str, frg::stl_allocator{}};
#else
	return std::string{str};
#endif
}

#ifdef TEST_FRIGG
template <template<typename...> typename Msg>
auto make_msg() {
	return Msg<frg::stl_allocator>{frg::stl_allocator{}};
}
#else
template <typename Msg>
auto make_msg() {
	return Msg{};
}
#endif

#ifdef TEST_FRIGG
template <template<typename...> typename Msg, typename ...Ts>
auto parse_with(Ts &&...ts) {
	if constexpr (sizeof...(ts) == 2)
		return bragi::parse_head_tail<Msg>(std::forward<Ts>(ts)..., frg::stl_allocator{});
	else
		return bragi::parse_head_only<Msg>(std::forward<Ts>(ts)..., frg::stl_allocator{});
}
#else
template <typename Msg, typename ...Ts>
auto parse_with(Ts &&...ts) {
	if constexpr (sizeof...(ts) == 2)
		return bragi::parse_head_tail<Msg>(std::forward<Ts>(ts)...);
	else
		return bragi::parse_head_only<Msg>(std::forward<Ts>(ts)...);
}
#endif

} // namespace test
