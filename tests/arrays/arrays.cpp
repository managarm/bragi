#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <arrays.bragi.frg.hpp>
#else
#include <arrays.bragi.std.hpp>
#endif

#include <cassert>

void test1() {
	auto t1 = test::make_msg<Test1>();
	t1.set_arr(test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF));

	assert(bragi::message_id<Test1> == 1);
	assert(bragi::head_size<Test1> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test1>(head_buf);
	assert(t2);

	auto arr = test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF);
	assert(t2->arr() == arr);
}

void test2() {
	auto t1 = test::make_msg<Test2>();
	t1.set_arr(test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF));

	assert(bragi::message_id<Test2> == 2);
	assert(bragi::head_size<Test2> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test2>(head_buf);
	assert(t2);

	auto arr = test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF, 0);
	assert(t2->arr() == arr);
}

void test3() {
	auto t1 = test::make_msg<Test3>();

	t1.set_arr(test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5)
	));

	assert(bragi::message_id<Test3> == 3);
	assert(bragi::head_size<Test3> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test3>(head_buf);
	assert(t2);

	auto arr = test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5)
	);

	assert(t2->arr() == arr);
}

void test4() {
	auto t1 = test::make_msg<Test4>();

	t1.set_arr1(test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5)
	));

	t1.set_arr2(test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5)
	));

	assert(bragi::message_id<Test4> == 4);
	assert(bragi::head_size<Test4> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test4>(head_buf);
	assert(t2);

	auto arr1 = test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF, 0),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE, 0),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5, 0)
	);

	auto arr2 = test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5),
		test::make_vector<uint8_t>(),
		test::make_vector<uint8_t>()
	);

	assert(t2->arr1() == arr1);
	assert(t2->arr2() == arr2);
}

void test5_1() {
	auto t1 = test::make_msg<Test5>();

	t1.set_arr(test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5)
	));

	assert(bragi::message_id<Test5> == 5);
	assert(bragi::head_size<Test5> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test5>(head_buf);
	assert(t2);

	auto arr = test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5),
		test::make_vector<uint8_t>(0, 0, 0, 0)
	);

	assert(t2->arr() == arr);
}

void test5_2() {
	auto t1 = test::make_msg<Test5>();

	t1.set_arr(test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5),
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF)
	));

	assert(bragi::message_id<Test5> == 5);
	assert(bragi::head_size<Test5> == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test5>(head_buf);
	assert(t2);

	auto arr = test::make_vector<test::vec_of<uint8_t>>(
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF),
		test::make_vector<uint8_t>(0xCA, 0xFE, 0xBA, 0xBE),
		test::make_vector<uint8_t>(0xB1, 0x6B, 0x00, 0xB5),
		test::make_vector<uint8_t>(0xDE, 0xAD, 0xBE, 0xEF)
	);

	assert(t2->arr() == arr);
}

int main() {
	test1();
	test2();
	test3();
	test4();
	test5_1();
	test5_2();
}
