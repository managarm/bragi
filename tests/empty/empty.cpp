#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <empty.bragi.frg.hpp>
#else
#include <empty.bragi.std.hpp>
#endif

#include <cassert>

void test_empty_head() {
	auto t1 = test::make_msg<TestEmptyHead>();
	t1.set_foo(test::make_string("TestEmptyHead"));

	assert(bragi::message_id<TestEmptyHead> == 1);
	assert(bragi::head_size<TestEmptyHead> == 128);
	assert(t1.size_of_head() == 8);
	assert(t1.size_of_tail() > 0);

	std::vector<std::byte> head_buf(128);
	std::vector<std::byte> tail_buf(t1.size_of_tail());
	assert(bragi::write_head_tail(t1, head_buf, tail_buf));

	auto t2 = test::parse_with<TestEmptyHead>(head_buf, tail_buf);
	assert(t2);

	assert(t2->foo() == test::make_string("TestEmptyHead"));
}

void test_empty_tail() {
	auto t1 = test::make_msg<TestEmptyTail>();
	t1.set_foo(test::make_string("TestEmptyTail"));

	assert(bragi::message_id<TestEmptyTail> == 2);
	assert(bragi::head_size<TestEmptyTail> == 128);
	assert(t1.size_of_head() > 8);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<TestEmptyTail>(head_buf);
	assert(t2);

	assert(t2->foo() == test::make_string("TestEmptyTail"));
}

void test_no_tail() {
	auto t1 = test::make_msg<TestNoTail>();
	t1.set_foo(test::make_string("TestNoTail"));

	assert(bragi::message_id<TestNoTail> == 3);
	assert(bragi::head_size<TestNoTail> == 128);
	assert(t1.size_of_head() > 8);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<TestNoTail>(head_buf);
	assert(t2);

	assert(t2->foo() == test::make_string("TestNoTail"));
}

void test_empty_message() {
	auto t1 = test::make_msg<TestEmptyMessage>();

	assert(bragi::message_id<TestEmptyMessage> == 4);
	assert(bragi::head_size<TestEmptyMessage> == 128);
	assert(t1.size_of_head() == 8);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<TestEmptyMessage>(head_buf);
	assert(t2);
}

int main() {
	test_empty_head();
	test_empty_tail();
	test_no_tail();
	test_empty_message();
}
