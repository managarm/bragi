#include <iostream>

#include <using.bragi.hpp>
#include <bragi/helpers-all.hpp>
#include <bragi/helpers-std.hpp>
#include <type_traits>
#include <cassert>

static_assert(std::is_same_v<Hello::World::Test, Bar::Foo>, "Test failed");
static_assert(std::is_same_v<Hello::World::Test, Hello::World::Foo>, "Test failed");
static_assert(std::is_same_v<Hello::World::Test, Foo>, "Test failed");

int main() { }
