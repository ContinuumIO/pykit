/*

IR inclusion file.

Type constructors can be used as follows:

    2d array of int32

        Array<Int32, 2>

    Tuple type of two values:

        Tuple<_list<Double, Bool>,>

    Note that we need a comma here, since two consecutive '>>' doesn't parse.

These can also be used in typedefs, declarations or casts:

    typedef Array<int *, 2> ArrayOfPointers;
    Array<int *, 2> x = y;
    x = (Array<int *, 2>) y;

*/

/* Dummy definition */
typedef struct { int _; } Type;

/* Special constructor to create a list */
typedef Type _list;

/* Constructors, i.e. Int<32, 1> */
typedef Type Integral;
typedef Type Real;
typedef Type Complex;
typedef Type Array;
typedef Type Struct;
typedef Type Pointer;
typedef Type ObjectT;
typedef Type BytesT;
typedef Type UnicodeT;
typedef Type CharT;
typedef Type UniCharT;
typedef Type Tuple;
typedef Type List;
typedef Type Dict;
typedef Type SumType;
typedef Type Partial;
typedef Type Function;
typedef Type Typedef;

/* Units */
typedef Type Void;
typedef Type Bool;
typedef Type Int8;
typedef Type Int16;
typedef Type Int32;
typedef Type Int64;
typedef Type UInt8;
typedef Type UInt16;
typedef Type UInt32;
typedef Type UInt64;

typedef Type Float32;
typedef Type Float64;

typedef Type Complex64;
typedef Type Complex128;

typedef Type Object;
typedef Type Bytes;
typedef Type Unicode;

/* Typedefs */
typedef Type Int;
typedef Type Long;
typedef Type LongLong;