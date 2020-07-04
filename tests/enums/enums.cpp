#include <iostream>

#include <enums.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <cassert>

int main() {
	Test t1;
	t1.set_foo(Foo::D);
	t1.set_bar(Bar::E);

	t1.set_foos({Foo::D, Foo::A, Foo::F, Foo::B});
	t1.set_bars({Bar::E, Bar::B, Bar::A, Bar::C});

	assert(Test::message_id == 1);
	assert(Test::head_size == 128);
	assert(t1.size_of_tail() == 0);

	assert(static_cast<int32_t>(Foo::A) == 1);
	assert(static_cast<int32_t>(Foo::B) == 2);
	assert(static_cast<int32_t>(Foo::C) == 4);
	assert(static_cast<int32_t>(Foo::D) == 2);
	assert(static_cast<int32_t>(Foo::E) == 3);
	assert(static_cast<int32_t>(Foo::F) == 4);

	assert(Bar::A == 1);
	assert(Bar::B == 2);
	assert(Bar::C == 4);
	assert(Bar::D == 2);
	assert(Bar::E == 3);
	assert(Bar::F == 4);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test>(head_buf);
	assert(t2);

	assert(t2->foo() == Foo::D);
	assert(t2->bar() == Bar::E);

	auto foos = std::vector{Foo::D, Foo::A, Foo::F, Foo::B};
	assert(t2->foos() == foos);

	auto bars = std::vector{Bar::E, Bar::B, Bar::A, Bar::C};
	assert(t2->bars() == bars);
}
