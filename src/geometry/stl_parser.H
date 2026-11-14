#ifndef PELE_STL_PARSER_H
#define PELE_STL_PARSER_H
#include <string>
#include <vector>
#include <cstdint>
namespace pele {
struct STLFacet { double normal[3]; double vertices[3][3]; };
class STLReader {
public:
    void read(const std::string& fname);
    const std::vector<STLFacet>& getFacets() const { return m_facets; }
    size_t numFacets() const { return m_facets.size(); }
private:
    void readASCII(const std::string& fname);
    void readBinary(const std::string& fname);
    std::vector<STLFacet> m_facets;
};
}
#endif