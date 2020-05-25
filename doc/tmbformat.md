everything is biiiig endian

sizeof(float) = 4

sizeof(int) = 4

sizeof(uint) = 4

sizeof(bool) = 1

####Header
MAX_CHUNKS = 2 right now
```
struct header_t
{
    uint magic; //54 4d 46 08
    uint version; //00 01
    uint mapVersion; //revision
    chunk_t chunks[MAX_CHUNKS]; //chunk dir
}
```
####Chunk directory
```
struct chunk_t
{
    char ident[8]; //8 character chunk identifier :)
    uint start; //start location (bytes) in file
    uint length; //length (bytes) in file
    uint reserved; //reserved, set to all zeros
}
```
####Chunks
#####Vertices
chunk 0

chunk id = "VERTICES"

an array of vertices

max = 0xFFFFFFFF
```
struct vector_t
{
    float x;
    float y;
    float z;
}
```
12 bytes
#####Planes
chunk 1

chunk id = "PLANES!!"

an array of planes

max = 0xFFFFFFFF
```
struct plane_t
{
    vector_t normal;
    vector_t point; //todo use D
}
```
24 bytes
#####BSPLeaf
chunk 2

chunk id = "BSPLEAF!"

todo

0 bytes
#####BSPNode
chunk 3

chunk id = "BSPNODE!"

todo

0 bytes
#####