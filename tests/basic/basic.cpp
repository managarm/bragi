#include <iostream>

#include <basic.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <cassert>

int main() {
	Test t1;
	t1.set_a(0xDEADBEEF);
	t1.set_b(0xDEADBEEFCAFEBABE);
	t1.set_c("Hello, world!");
	t1.set_d(1337);
	t1.set_e({1, 2, 3, 4, 5, 6, 7, 8, 9, 0});

	assert(Test::message_id == 1);
	assert(Test::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test>(head_buf);
	assert(t2);

	assert(t2->a() == 0xDEADBEEF);
	assert(t2->b() == 0xDEADBEEFCAFEBABE);
	assert(t2->c() == "Hello, world!");
	assert(t2->d() == 1337);
	auto test = std::vector<uint8_t>{1, 2, 3, 4, 5, 6, 7, 8, 9, 0};
	assert(t2->e() == test);
}
