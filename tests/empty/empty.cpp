#include <iostream>

#include <empty.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <cassert>

void test_empty_head() {
	TestEmptyHead t1;
	t1.set_foo("TestEmptyHead");

	assert(TestEmptyHead::message_id == 1);
	assert(TestEmptyHead::head_size == 128);
	assert(t1.size_of_head() == 8);
	assert(t1.size_of_tail() > 0);

	std::vector<std::byte> head_buf(128);
	std::vector<std::byte> tail_buf(t1.size_of_tail());
	assert(bragi::write_head_tail(t1, head_buf, tail_buf));

	auto t2 = bragi::parse_head_tail<TestEmptyHead>(head_buf, tail_buf);
	assert(t2);

	assert(t2->foo() == "TestEmptyHead");
}

void test_empty_tail() {
	TestEmptyTail t1;
	t1.set_foo("TestEmptyTail");

	assert(TestEmptyTail::message_id == 2);
	assert(TestEmptyTail::head_size == 128);
	assert(t1.size_of_head() > 8);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<TestEmptyTail>(head_buf);
	assert(t2);

	assert(t2->foo() == "TestEmptyTail");
}

void test_no_tail() {
	TestNoTail t1;
	t1.set_foo("TestNoTail");

	assert(TestNoTail::message_id == 3);
	assert(TestNoTail::head_size == 128);
	assert(t1.size_of_head() > 8);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<TestNoTail>(head_buf);
	assert(t2);

	assert(t2->foo() == "TestNoTail");
}

void test_empty_message() {
	TestEmptyMessage t1;

	assert(TestEmptyMessage::message_id == 4);
	assert(TestEmptyMessage::head_size == 128);
	assert(t1.size_of_head() == 8);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<TestEmptyMessage>(head_buf);
	assert(t2);
}

int main() {
	test_empty_head();
	test_empty_tail();
	test_no_tail();
	test_empty_message();
}
