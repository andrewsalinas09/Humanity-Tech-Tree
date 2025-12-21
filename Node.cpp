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
    ORGANIZATION,              // "The Royal Society"
    GEOPOLITICAL_ENTITY,

    WORK_PUBLICATION, //Books, publications
    LEGISLATION,     // "Copyright", "Resource Shortage"

    HISTORICAL_EVENT,              // "WWII"
    SOCIETAL_ERA,
    BELIEF_SYSTEM,       // "Miasma", "Geocentrism"

    SOCIETAL_NEED,      // "Faster Travel", "Shelter", "Food Preservation"

    // --- TIER 1: THE DRIVERS (Why?) ---
    NATURAL_LAW,        // "Thermodynamics", "Electromagnetism"
    FORMAL_CONCEPT,     // "Boolean Logic", "Geometry"
    CAPABILITY,         // "Precision < 0.01mm", "Global Instant Comms"


    // --- TIER 2: THE ENABLERS (How?) ---
    MATERIAL,           // "Steel", "Silicon", "Rubber", "Vulcanized Rubber"
    METHOD_TECHNIQUE,   // "Casting", "Photolithography", "Triangulation"
    STANDARD_UNIT,      // "The Meter", "TCP/IP Protocol", "IEEE 802.11"

    // --- TIER 3: THE BUILDERS (The recursive part) ---
    // These are distinct because they are used *during* creation but don't end up inside the product.
    TOOL_INSTRUMENT,    // "Lathe", "Oscilloscope", "Compiler", "Surface Plate"

    // --- TIER 4: THE TECHNOLOGY (The What?) ---
    COMPONENT,          // "Piston", "Transistor", "WiFi Chipset" (Parts)
    TECH_PARADIGM,      // "Internal Combustion Engine", "Smartphone", "Internet" (The Abstract Machine)

    // --- TIER 5: THE INSTANCE (The Real Thing) ---
    ARTIFACT            // "Ford Model T", "iPhone 1", "Intel 4004"

};

enum class EdgeType {
    // ==========================================
    // GROUP 1: THE HARD TECH TREE (The "Must Haves")
    // ==========================================
    // These dictate if a technology works.

    MAKES_POSSIBLE,      // Physics -> Capability ("Optics" MAKES_POSSIBLE "Magnification")
    IS_COMPONENT_OF,     // Component -> Paradigm ("Lens" IS_COMPONENT_OF "Telescope")
    IS_INGREDIENT_OF,    // Material -> Component ("Glass" IS_INGREDIENT_OF "Lens")
    OPTIMIZES,           // Tool -> Method ("Lathe" OPTIMIZES "Turning")
    IMPLEMENTS,          // Artifact -> Paradigm ("Hubble" IMPLEMENTS "Space Telescope")

    // ==========================================
    // GROUP 2: THE HUMAN CONTEXT (The "Who & When")
    // ==========================================
    // These connect People to the Tree.

    // --- Origin Stories ---
    AUTHORED,            // Person -> Work ("Newton" AUTHORED "Principia")
    DISCOVERED,          // Person -> Natural_Law ("Archimedes" DISCOVERED "Buoyancy")
                         // *Use this if they didn't write a specific book, or as a shorthand.*
    INVENTED,            // Person -> Tech_Paradigm ("Bell" INVENTED "Telephone")

    // --- Intellectual Lineage ---
    INFLUENCED_BY,       // Person -> Person ("Aristotle" INFLUENCED_BY "Plato")
    STUDIED_AT,          // Person -> Org ("Newton" STUDIED_AT "Cambridge")

    // --- The "Time Gate" ---
    REQUIRES_KNOWLEDGE,  // Person -> Concept ("Newton" REQUIRES_KNOWLEDGE "Algebra")
                         // *Validation Rule: A Person cannot exist before their required knowledge.*

    // ==========================================
    // GROUP 3: EVOLUTION & CONFLICT (The "Story")
    // ==========================================
    // These describe how ideas change over time.

    // --- Transition ---
    REPLACES,            // Paradigm -> Paradigm ("Transistor" REPLACES "Vacuum Tube")
                         // *UI Logic: Often implies the old one stops being used.*
    SUPERSEDES,          // Law -> Law ("Relativity" SUPERSEDES "Newtonian Gravity")
                         // *Note: The old one is still useful (Newton), but less accurate.*

    // --- Conflict ---
    DISPROVES,           // Concept -> Belief ("Germ Theory" DISPROVES "Miasma")
    INHIBITS,            // Belief -> Concept ("Geocentrism" INHIBITS "Astronomy")

    // --- Motivation ---
    MOTIVATED_BY,        // Concept -> Concept ("Chemistry" MOTIVATED_BY "Alchemy")
                         // *Use when the predecessor was "wrong" but led to the right path.*
    DRIVEN_BY_NEED,      // Paradigm -> Societal_Need ("Vaccines" DRIVEN_BY_NEED "Smallpox")

};enum class ValidityStatus {
    CURRENT_TRUTH,      // (Germ Theory)
    DISPROVEN,          // (Phlogiston)
    SUPERSEDED,         // (Newtonian Physics)
    HYPOTHETICAL,       // (String Theory)
    SUBJECTIVE          // (Modernism)
};

enum class EpistemicStatus {
    // --- The History Books ---
    MAINSTREAM_FACT,    // "Egyptians built Pyramids" (Default)
    HIGH_CONFIDENCE,    // "Vikings reached America" (Accepted theory)

    // --- The Edge Cases ---
    DEBATED,            // "Shakespeare authorship question"
    UNCERTAIN_ORIGIN,   // "Who invented the compass first?"

    // --- The "User Filter" Zone ---
    FRINGE_THEORY,      // "Aliens built Pyramids", "Phantom Time Hypothesis"
    MYTHOLOGY,          // "Prometheus gave fire to humans"
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

    EpistemicStatus truth_level;

    // --- THE LOGIC (The Math) ---
    // If empty/null: This is a MANDATORY requirement (AND).
    // If set (0, 1, 2): This is part of an ALTERNATIVE path (OR).
    std::optional<int> alternative_path_id;
    


    // --- Simulation Data ---
    float impact_weight;        // 0.0 - 1.0

    // --- Metadata ---
    std::string justification;
    std::vector<std::string> source_urls;
};