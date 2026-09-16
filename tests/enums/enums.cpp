#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <enums.bragi.frg.hpp>
#else
#include <enums.bragi.std.hpp>
#endif

#include <cassert>

void test1() {
	auto t1 = test::make_msg<Test>();
	t1.set_foo(Foo::D);
	t1.set_bar(Bar::E);

	t1.set_foos(test::make_vector<Foo>(Foo::D, Foo::A, Foo::F, Foo::B));
	t1.set_bars(std::array<uint8_t, 4>{Bar::E, Bar::B, Bar::A, Bar::C});

	assert(bragi::message_id<Test> == 1);
	assert(bragi::head_size<Test> == 128);
	assert(t1.size_of_tail() == 0);

	assert(static_cast<int32_t>(Foo::A) == 1);
	assert(static_cast<int32_t>(Foo::B) == 2);
	assert(static_cast<int32_t>(Foo::C) == 4);
	assert(static_cast<int32_t>(Foo::D) == 5);
	assert(static_cast<int32_t>(Foo::E) == 6);
	assert(static_cast<int32_t>(Foo::F) == 7);

	assert(Bar::A == 1);
	assert(Bar::B == 2);
	assert(Bar::C == 4);
	assert(Bar::D == 2);
	assert(Bar::E == 3);
	assert(Bar::F == 4);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test>(head_buf);
	assert(t2);

	assert(t2->foo() == Foo::D);
	assert(t2->bar() == Bar::E);

	auto foos = test::make_vector<Foo>(Foo::D, Foo::A, Foo::F, Foo::B);
	assert(t2->foos() == foos);

	auto bars = std::array<uint8_t, 4>{Bar::E, Bar::B, Bar::A, Bar::C};
	assert(t2->bars() == bars);
}

void test2() {
	auto n = test::make_msg<Nested>();
	n.set_bar(Bar::E);
	n.set_bars(test::make_vector<uint8_t>(Bar::A, Bar::C, Bar::F));
	n.set_baz(Baz::B);
	n.set_bazs(test::make_vector<uint32_t>(Baz::A, Baz::B));
	n.set_foo(Foo::C);
	n.set_foos(test::make_vector<Foo>(Foo::A, Foo::F));

	auto t1 = test::make_msg<Test2>();
	t1.set_nested(n);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test2>(head_buf);
	assert(t2);

	assert(t2->nested().bar() == Bar::E);
	auto bars = test::make_vector<uint8_t>(Bar::A, Bar::C, Bar::F);
	assert(t2->nested().bars() == bars);
	assert(t2->nested().baz() == Baz::B);
	auto bazs = test::make_vector<uint32_t>(Baz::A, Baz::B);
	assert(t2->nested().bazs() == bazs);
	assert(t2->nested().foo() == Foo::C);
	auto foos = test::make_vector<Foo>(Foo::A, Foo::F);
	assert(t2->nested().foos() == foos);
}

int main() {
	test1();
	test2();
}
