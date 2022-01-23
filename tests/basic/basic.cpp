#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <basic.bragi.frg.hpp>
#else
#include <basic.bragi.std.hpp>
#endif

#include <cassert>

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
}
