#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <preamble.bragi.frg.hpp>
#else
#include <preamble.bragi.std.hpp>
#endif

#include <cassert>

void expect_foo(const std::vector<std::byte> &head) {
	auto preamble = bragi::read_preamble(head);
	assert(!preamble.error());
	assert(preamble.id() == bragi::message_id<Foo>);
	assert(preamble.tail_size() == 0);

	auto t = test::parse_with<Foo>(head);
	assert(t);
	assert(t->foo() == test::make_string("Hello..."));
}

void expect_bar(const std::vector<std::byte> &head, const std::vector<std::byte> &tail) {
	auto preamble = bragi::read_preamble(head);
	assert(!preamble.error());
	assert(preamble.id() == bragi::message_id<Bar>);
	assert(preamble.tail_size() == 4);

	auto t = test::parse_with<Bar>(head, tail);
	assert(t);
	assert(t->bar() == test::make_string("...world!"));
	assert(t->baz() == 123456789);
}

void test_foo() {
	auto t = test::make_msg<Foo>();
	t.set_foo(test::make_string("Hello..."));

	assert(bragi::message_id<Foo> == 1);
	assert(bragi::head_size<Foo> == 128);
	assert(t.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t, head_buf));

	expect_foo(head_buf);
}

void test_bar() {
	auto t = test::make_msg<Bar>();
	t.set_bar(test::make_string("...world!"));
	t.set_baz(123456789);

	assert(bragi::message_id<Bar> == 2);
	assert(bragi::head_size<Bar> == 128);
	assert(t.size_of_tail() == 4);

	std::vector<std::byte> head_buf(128);
	std::vector<std::byte> tail_buf(t.size_of_tail());
	assert(bragi::write_head_tail(t, head_buf, tail_buf));

	expect_bar(head_buf, tail_buf);
}

int main() {
	test_foo();
	test_bar();
}
