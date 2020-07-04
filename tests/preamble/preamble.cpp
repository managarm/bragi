#include <iostream>

#include <preamble.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <cassert>

void expect_foo(const std::vector<std::byte> &head) {
	auto preamble = bragi::read_preamble(head);
	assert(!preamble.error());
	assert(preamble.id() == Foo::message_id);
	assert(preamble.tail_size() == 0);

	auto t = bragi::parse_head_only<Foo>(head);
	assert(t);
	assert(t->foo() == "Hello...");
}

void expect_bar(const std::vector<std::byte> &head, const std::vector<std::byte> &tail) {
	auto preamble = bragi::read_preamble(head);
	assert(!preamble.error());
	assert(preamble.id() == Bar::message_id);
	assert(preamble.tail_size() == 4);

	auto t = bragi::parse_head_tail<Bar>(head, tail);
	assert(t);
	assert(t->bar() == "...world!");
	assert(t->baz() == 123456789);
}

void test_foo() {
	Foo t;
	t.set_foo("Hello...");

	assert(Foo::message_id == 1);
	assert(Foo::head_size == 128);
	assert(t.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t, head_buf));

	expect_foo(head_buf);
}

void test_bar() {
	Bar t;
	t.set_bar("...world!");
	t.set_baz(123456789);

	assert(Bar::message_id == 2);
	assert(Bar::head_size == 128);
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
