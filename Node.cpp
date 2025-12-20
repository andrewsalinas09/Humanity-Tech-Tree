#include <string>
#include <vector>
#include <map>
#include <optional>

// ==========================================
// 1. CLASSIFICATION ENUMS
// ==========================================

enum class NodeCategory {
    // --- The Actors ---
    PERSON,             // "Isaac Newton"
    GROUP,              // "The Royal Society"

    // --- The Artifacts ---
    INVENTION,          // "Steam Engine"
    DISCOVERY,          // "Gravity"
    EVENT,              // "WWII"
    CONCEPT,            // "Calculus", "Binary Logic"
    LAW_CONSTRAINT,     // "Copyright", "Resource Shortage"
    BELIEF_SYSTEM       // "Miasma", "Geocentrism"
};

enum class EdgeType {
    // --- Causality (Artifact -> Artifact) ---
    HARD_REQ,           // Impossible without (Transistor -> CPU)
    COMPONENT_OF,       // (Tire -> Car)
    
    // --- Optimization (The "Lathe" Loop Solution) ---
    // Implies: "Target works without Source, but is inefficient."
    OPTIMIZATION_FACTOR, 

    INHIBITOR, // Dogma -> Astronomy
    MOTIVATED_BY, // "Psychohistory" (Miasma -> Sewer Systems)
    
    // --- Origins (Person -> Artifact) ---
    // Covers both "Invented" and "Discovered"
    DISCOVERED_BY,      // (Newton -> Calculus)
    
    // --- Genealogy (Root -> Person) ---
    MEMBER_OF,          // (Humanity -> Newton) or (Royal Society -> Newton)
    EDUCATED_BY, // What school they went to
    INFLUENCED_BY, // Who their mentors were
    REQUIRES_KNOWLEDGE, // Newton requires having known algebra, geometry, etc...

    // --- Intellectual ---
    INSPIRATION,        // Idea transfer only
    DISPROVES,           // (Oxygen -> Phlogiston)
    REPLACES, // DVD -> BluRay
};

enum class ValidityStatus {
    CURRENT_TRUTH,      // (Germ Theory)
    DISPROVEN,          // (Phlogiston)
    SUPERSEDED,         // (Newtonian Physics)
    HYPOTHETICAL,       // (String Theory)
    SUBJECTIVE          // (Modernism)
};

// ==========================================
// 2. TEMPORAL & SPATIAL STRUCTS
// ==========================================

struct FuzzyTime {
    long long year_start;   // Year (Negative for BCE)
    std::optional<long long> year_end; // Null if still active/alive
    
    // String for UI display logic (e.g. "Late 14th Century")
    std::string display_string; 
};

struct RegionalAvailability {
    // Where is this active?
    std::string region_id;      // "geo:china", "geo:europe"
    
    // When was it active HERE? 
    // Note: Multiple entries for the same region allow for "Dark Ages" 
    // (e.g. Concrete lost in Europe then found again).
    FuzzyTime local_timeline;   
    
    // Provenance
    bool is_indigenous;         // Did it start here?
    std::string import_source;  // If false, where did it come from? ("geo:china")
};

struct ResourceCost {
    // Normalized 0.0 - 1.0 for simulation difficulty
    float labor_intensity;  
    float knowledge_depth;  
    float resource_rarity;  
};

// ==========================================
// 3. THE NODE
// ==========================================

struct HistoryNode {
    // --- Identity ---
    std::string id;             // UUID
    std::string wikidata_id;    // "Q12345"
    std::string slug;           // "steam-engine"
    
    // --- Core Data ---
    std::string name;
    NodeCategory category;
    ValidityStatus validity;
    
    // --- Simulation Properties ---
    // This vector handles the "Gunpowder" problem.
    // One node, multiple start dates depending on location.
    std::vector<RegionalAvailability> availability;
    
    ResourceCost base_cost;
    int zoom_level;             // 1=Era, 2=Major, 3=Detail
    
    // --- Loop Handling ---
    // Allows UI to stack "Steel I", "Steel II" visually.
    std::optional<std::string> variant_group_id; 
    int tech_generation;        

    // --- Content ---
    std::string wiki_summary;
    std::string image_url;
};

// ==========================================
// 4. THE EDGE
// ==========================================

struct DependencyEdge {
    std::string id;
    std::string from_node_id;
    std::string to_node_id;
    
    EdgeType type;
    
    // --- The "Leibniz" Solution ---
    // If multiple edges go to the same Target with the same type,
    // they are usually "AND" requirements.
    // IF they share a discovery_group_id, they are "OR" (Independent Discovery).
    // -1 = Standard Logic (AND)
    //  0 = Newton's Group
    //  1 = Leibniz's Group
    int discovery_group_id; 

    // --- Simulation Data ---
    float impact_weight;        // 0.0 - 1.0
    
    // --- Metadata ---
    std::string justification;
    std::vector<std::string> source_urls;
};