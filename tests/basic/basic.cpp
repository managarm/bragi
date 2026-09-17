#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <basic.bragi.frg.hpp>
#else
#include <basic.bragi.std.hpp>
#endif

#include <cassert>

void test_unknown_tag() {
	auto t1 = test::make_msg<Test>();
	t1.set_a(1);
	t1.set_d(2);

	std::vector<std::byte> head_buf(t1.size_of_head());
	assert(bragi::write_head_only(t1, head_buf));

	// Rewrite the tag of the first tags-block entry to one that is not declared.
	auto ptr = static_cast<uint8_t>(head_buf[21]);
	assert(static_cast<uint8_t>(head_buf[ptr]) == (2 * 1 + 1));
	head_buf[ptr] = static_cast<std::byte>(2 * 63 + 1);

	assert(!test::parse_with<Test>(head_buf));
}

void test_oversized_head() {
	auto t1 = test::make_msg<Test>();
	t1.set_c(test::make_string(std::string(bragi::head_size<Test>, 'x').c_str()));

	assert(t1.size_of_head() > bragi::head_size<Test>);

	std::vector<std::byte> head_buf(t1.size_of_head());
	assert(!bragi::write_head_only(t1, head_buf));
}

int main() {
	auto t1 = test::make_msg<Test>();
	t1.set_a(0xDEADBEEF);
	t1.set_b(0xDEADBEEFCAFEBABE);
	t1.set_c(test::make_string("Hello, world!"));
	t1.set_d(1337);
	t1.set_e(test::make_vector<uint8_t>(1, 2, 3, 4, 5, 6, 7, 8, 9, 0));

	assert(bragi::message_id<Test> == 1);
	assert(bragi::head_size<Test> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test>(head_buf);
	assert(t2);

	assert(t2->a() == 0xDEADBEEF);
	assert(t2->b() == 0xDEADBEEFCAFEBABE);
	assert(t2->c() == test::make_string("Hello, world!"));
	assert(t2->d() == 1337);
	auto test = test::make_vector<uint8_t>(1, 2, 3, 4, 5, 6, 7, 8, 9, 0);
	assert(t2->e() == test);
	test_unknown_tag();
	test_oversized_head();
}
