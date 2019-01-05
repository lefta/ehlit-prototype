struct test_struct {
    int field1;
    char* field2;
};

typedef struct {
    int field1;
} test_struct_t;

struct linked_list {
    void* contents;
    linked_list* next;
};

struct forward_decl;
