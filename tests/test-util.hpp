#pragma once

#include <bragi/helpers-all.hpp>
#include <utility>

#ifdef TEST_FRIGG
#include <bragi/helpers-frigg.hpp>
#include <frg/std_compat.hpp>
#include <frg/vector.hpp>
#include <frg/string.hpp>
#else
#include <bragi/helpers-std.hpp>
#include <vector>
#include <string>
#endif

namespace test {

#ifdef TEST_FRIGG

struct test_allocator {
	test_allocator(int) {}

	void *allocate(size_t sz) { return operator new(sz); }
	void free(void *ptr) { operator delete(ptr); }
	void deallocate(void *ptr, size_t sz) { operator delete(ptr, sz); }
};

template <typename T>
using vec_of = frg::vector<T, test_allocator>;

#else

template <typename T>
using vec_of = std::vector<T>;

#endif

template <typename T, typename ...Ts>
auto make_vector(Ts &&...ts) {
#ifdef TEST_FRIGG
	frg::vector<T, test_allocator> vec{test_allocator{1}};

	(vec.push_back(std::forward<Ts>(ts)), ...);

	return vec;
#else
	return std::vector<T>{std::forward<Ts>(ts)...};
#endif
}

auto make_string(const char *str) {
#ifdef TEST_FRIGG
	return frg::string<test_allocator>{str, test_allocator{1}};
#else
	return std::string{str};
#endif
}

#ifdef TEST_FRIGG
template <template<typename...> typename Msg>
auto make_msg() {
	return Msg<test_allocator>{test_allocator{1}};
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
		return bragi::parse_head_tail<Msg>(std::forward<Ts>(ts)..., test_allocator{1});
	else
		return bragi::parse_head_only<Msg>(std::forward<Ts>(ts)..., test_allocator{1});
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
