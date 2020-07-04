#include <iostream>

#include <arrays.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <cassert>

void test1() {
	Test1 t1;
	t1.set_arr({0xDE, 0xAD, 0xBE, 0xEF});

	assert(Test1::message_id == 1);
	assert(Test1::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test1>(head_buf);
	assert(t2);

	auto arr = std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF};
	assert(t2->arr() == arr);
}

void test2() {
	Test2 t1;
	t1.set_arr({0xDE, 0xAD, 0xBE, 0xEF});

	assert(Test2::message_id == 2);
	assert(Test2::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test2>(head_buf);
	assert(t2);

	auto arr = std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF, 0};
	assert(t2->arr() == arr);
}

void test3() {
	Test3 t1;
	t1.set_arr({
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5}
	});

	assert(Test3::message_id == 3);
	assert(Test3::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test3>(head_buf);
	assert(t2);

	auto arr = std::vector<std::vector<uint8_t>>{
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5}
	};

	assert(t2->arr() == arr);
}

void test4() {
	Test4 t1;
	t1.set_arr1({
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5}
	});

	t1.set_arr2({
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5}
	});

	assert(Test4::message_id == 4);
	assert(Test4::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test4>(head_buf);
	assert(t2);

	auto arr1 = std::vector<std::vector<uint8_t>>{
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF, 0},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE, 0},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5, 0}
	};

	auto arr2 = std::vector<std::vector<uint8_t>>{
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5},
		std::vector<uint8_t>{},
		std::vector<uint8_t>{}
	};

	assert(t2->arr2() == arr2);
}

void test5_1() {
	Test5 t1;
	t1.set_arr({
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00}
	});

	assert(Test5::message_id == 5);
	assert(Test5::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test5>(head_buf);
	assert(t2);

	auto arr = std::vector<std::vector<uint8_t>>{
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0},
		std::vector<uint8_t>{0, 0, 0, 0}
	};

	assert(t2->arr() == arr);
}

void test5_2() {
	Test5 t1;
	t1.set_arr({
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5},
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF}
	});

	assert(Test5::message_id == 5);
	assert(Test5::head_size == 128);
	assert(t1.size_of_tail() == 0);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = bragi::parse_head_only<Test5>(head_buf);
	assert(t2);

	auto arr = std::vector<std::vector<uint8_t>>{
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF},
		std::vector<uint8_t>{0xCA, 0xFE, 0xBA, 0xBE},
		std::vector<uint8_t>{0xB1, 0x6B, 0x00, 0xB5},
		std::vector<uint8_t>{0xDE, 0xAD, 0xBE, 0xEF}
	};

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
