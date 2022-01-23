#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <using.bragi.frg.hpp>
#else
#include <using.bragi.std.hpp>
#endif

static_assert(bragi::message_id<Hello::World::Test> == bragi::message_id<Bar::Foo>, "Test failed");
static_assert(bragi::message_id<Hello::World::Test> == bragi::message_id<Hello::World::Foo>, "Test failed");
static_assert(bragi::message_id<Hello::World::Test> == bragi::message_id<Foo>, "Test failed");

int main() { }
