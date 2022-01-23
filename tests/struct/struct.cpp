#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <struct.bragi.frg.hpp>
#else
#include <struct.bragi.std.hpp>
#endif

#include <cassert>

void test1() {
	auto f = test::make_msg<Foo>();
	f.set_a(test::make_string("Hello"));
	f.set_b(0xDEADBEEFCAFEBABE);
	f.set_c(0xDEADBEEF);
	f.set_d(test::make_vector<uint8_t>(1, 2, 3, 4));

	auto t1 = test::make_msg<Test1>();
	t1.set_foo(f);

	assert(bragi::message_id<Test1> == 1);
	assert(bragi::head_size<Test1> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test1>(head_buf);
	assert(t2);

	assert(t2->foo().a() == test::make_string("Hello"));
	assert(t2->foo().b() == 0xDEADBEEFCAFEBABE);
	assert(t2->foo().c() == 0xDEADBEEF);
	auto test = test::make_vector<uint8_t>(1, 2, 3, 4);
	assert(t2->foo().d() == test);
}

void test2() {
	auto t1 = test::make_msg<Test2>();

	auto b1 = test::make_msg<Bar>();
	b1.set_a(test::make_string("Hello"));
	b1.set_b(1);
	t1.add_bars(b1);

	auto b2 = test::make_msg<Bar>();
	b2.set_a(test::make_string("World"));
	b2.set_b(2);
	t1.add_bars(b2);

	assert(bragi::message_id<Test2> == 2);
	assert(bragi::head_size<Test2> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test2>(head_buf);
	assert(t2);

	assert(t2->bars().size() == 2);

	assert(t2->bars()[0].a() == test::make_string("Hello"));
	assert(t2->bars()[1].a() == test::make_string("World"));

	assert(t2->bars()[0].b() == 1);
	assert(t2->bars()[1].b() == 2);
}

void test3() {
	auto t1 = test::make_msg<Test3>();

	auto b1 = test::make_msg<Baz>();
	auto b2 = test::make_msg<Bar>();
	b2.set_a(test::make_string("Hello"));
	b2.set_b(1);
	b1.set_bar(b2);

	auto f1 = test::make_msg<Foo>();
	auto f2 = test::make_msg<Foo>();
	f1.set_a(test::make_string("World"));
	f1.set_b(0xDEADBEEFCAFEBABE);
	f1.set_c(0xDEADBEEF);
	f1.set_d(test::make_vector<uint8_t>(1, 2, 3, 4));
	b1.add_foos(f1);

	f2.set_a(test::make_string("Testing"));
	f2.set_b(12345678901234567890u);
	f2.set_c(0xCAFEBABE);
	f2.set_d(test::make_vector<uint8_t>(5, 6, 7, 8));
	b1.add_foos(f2);

	t1.set_baz(b1);

	assert(bragi::message_id<Test3> == 3);
	assert(bragi::head_size<Test3> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test3>(head_buf);
	assert(t2);

	assert(t2->baz().foos().size() == 2);

	assert(t2->baz().bar().a() == test::make_string("Hello"));
	assert(t2->baz().foos()[0].a() == test::make_string("World"));
	assert(t2->baz().foos()[1].a() == test::make_string("Testing"));

	assert(t2->baz().bar().b() == 1);
	assert(t2->baz().foos()[0].b() == 0xDEADBEEFCAFEBABE);
	assert(t2->baz().foos()[1].b() == 12345678901234567890u);

	assert(t2->baz().foos()[0].c() == 0xDEADBEEF);
	assert(t2->baz().foos()[1].c() == 0xCAFEBABE);

	auto d1 = test::make_vector<uint8_t>(1, 2, 3, 4);
	auto d2 = test::make_vector<uint8_t>(5, 6, 7, 8);

	assert(t2->baz().foos()[0].d() == d1);
	assert(t2->baz().foos()[1].d() == d2);
}

int main() {
	test1();
	test2();
	test3();
}
