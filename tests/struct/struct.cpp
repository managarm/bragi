#include <iostream>

#include <struct.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <cassert>

void test1() {
	Foo f;
	f.set_a("Hello");
	f.set_b(0xDEADBEEFCAFEBABE);
	f.set_c(0xDEADBEEF);
	f.set_d({1, 2, 3, 4});

	Test1 t1;
	t1.set_foo(f);

	assert(Test1::message_id == 1);
	assert(Test1::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test1>(head_buf);
	assert(t2);

	assert(t2->foo().a() == "Hello");
	assert(t2->foo().b() == 0xDEADBEEFCAFEBABE);
	assert(t2->foo().c() == 0xDEADBEEF);
	auto test = std::vector<uint8_t>{1, 2, 3, 4};
	assert(t2->foo().d() == test);
}

void test2() {
	Test2 t1;

	Bar b1;
	b1.set_a("Hello");
	b1.set_b(1);
	t1.add_bars(b1);

	Bar b2;
	b2.set_a("World");
	b2.set_b(2);
	t1.add_bars(b2);

	assert(Test2::message_id == 2);
	assert(Test2::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test2>(head_buf);
	assert(t2);

	assert(t2->bars().size() == 2);

	assert(t2->bars()[0].a() == "Hello");
	assert(t2->bars()[1].a() == "World");

	assert(t2->bars()[0].b() == 1);
	assert(t2->bars()[1].b() == 2);
}

void test3() {
	Test3 t1;

	Baz b1;
	Bar b2;
	b2.set_a("Hello");
	b2.set_b(1);
	b1.set_bar(b2);

	Foo f1;
	f1.set_a("World");
	f1.set_b(0xDEADBEEFCAFEBABE);
	f1.set_c(0xDEADBEEF);
	f1.set_d({1, 2, 3, 4});
	b1.add_foos(f1);

	Foo f2;
	f2.set_a("Testing");
	f2.set_b(12345678901234567890u);
	f2.set_c(0xCAFEBABE);
	f2.set_d({5, 6, 7, 8});
	b1.add_foos(f2);

	t1.set_baz(b1);

	assert(Test3::message_id == 3);
	assert(Test3::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test3>(head_buf);
	assert(t2);

	assert(t2->baz().foos().size() == 2);

	assert(t2->baz().bar().a() == "Hello");
	assert(t2->baz().foos()[0].a() == "World");
	assert(t2->baz().foos()[1].a() == "Testing");

	assert(t2->baz().bar().b() == 1);
	assert(t2->baz().foos()[0].b() == 0xDEADBEEFCAFEBABE);
	assert(t2->baz().foos()[1].b() == 12345678901234567890u);

	assert(t2->baz().foos()[0].c() == 0xDEADBEEF);
	assert(t2->baz().foos()[1].c() == 0xCAFEBABE);

	std::vector<uint8_t> d1 = {1, 2, 3, 4};
	std::vector<uint8_t> d2 = {5, 6, 7, 8};

	assert(t2->baz().foos()[0].d() == d1);
	assert(t2->baz().foos()[1].d() == d2);
}

int main() {
	test1();
	test2();
	test3();
}
