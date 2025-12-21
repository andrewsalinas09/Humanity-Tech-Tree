#include <string>
#include <vector>
#include <map>
#include <optional>

// ==========================================
// 1. CLASSIFICATION ENUMS
// ==========================================

enum class NodeCategory {
    // --- Roots ---
    BIOLOGICAL_ENTITY,             // "Isaac Newton", "Humanity", "Aliens"
    // note that earth, mars, moon, universe are under natural phenomenon

    // --- The Actors ---
    ORGANIZATION,              // "The Royal Society"
    GEOPOLITICAL_ENTITY,

    WORK_PUBLICATION, //Books, publications
    LEGISLATION,     // "Copyright", "Resource Shortage"

    HISTORICAL_EVENT,              // "WWII"
    SOCIETAL_ERA,
    BELIEF_SYSTEM,       // "Miasma", "Geocentrism"

    SOCIETAL_NEED,      // "Faster Travel", "Shelter", "Food Preservation"

    NATURAL_PHENOMENON, // Malaria, Winter, Drought, The Tides, Hurricanes

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
    //TOOL_INSTRUMENT,    // "Lathe", "Oscilloscope", "Compiler", "Surface Plate"

    // --- TIER 4: THE TECHNOLOGY (The What?) ---
    //COMPONENT,          // "Piston", "Transistor", "WiFi Chipset" (Parts)
    TECHNOLOGY,      // "Internal Combustion Engine", "Smartphone", "Internet" (The Abstract Machine) // also includes tool/instrument/component/artifact

    // --- TIER 5: THE INSTANCE (The Real Thing) ---
    // ARTIFACT            // "Ford Model T", "iPhone 1", "Intel 4004"

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

    CONFORMS_TO // IEEE 754
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
    PRECIPATED,         // Assassination of ferdinate -> world war I, stock market crash of 1929 -> great depression
    GAVE_RISE_TO, // the blues -> jazz, prohibition -> organized crime

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

// Distinguishes the "Texture" of time
enum class TimeScale {
    GEOLOGICAL,     // "2 Million Years Ago" (Stone Tools) - Huge error bars
    ARCHAEOLOGICAL, // "Bronze Age" - Dated by strata/carbon
    HISTORICAL,     // "July 4, 1776" - Written records
    MYTHOLOGICAL    // "Before Time" / "The Creation" (For 'Belief' nodes)
};

// A single point in time with error bars
struct DatePoint {
    // We use a signed double for the "True Year"
    // Negative = BCE, Positive = CE.
    // Example: -3000.0 is 3000 BC. 2024.5 is June 2024.
    double year;

    // The "Fuzziness"
    // 0 = Exact Date (July 16, 1945)
    // 50 = "c. 1200 BC" (Could be 1250 or 1150)
    // 10000 = "Paleolithic"
    double uncertainty_range;

    TimeScale scale;
};

enum class KnowledgeStatus {
    ACTIVE,         // People use this daily (Smartphones today)
    THEORETICAL,    // Concept exists, but not built (Leonardo's Tank)
    LOST,           // Knowledge exists in ruins/books, but nobody can do it (Roman Concrete in 600 AD)
    OBSOLETE,       // We know how, but we chose not to (Steam Locomotives)
    MYTHICAL        // "Tower of Babel" - Exists in culture, not reality
};

struct TimeSegment {
    DatePoint start;
    std::optional<DatePoint> end; // Null = Ongoing

    KnowledgeStatus status;

    // Why did it end/start?
    // "Fall of Rome", "Library of Alexandria Burned", "Renaissance"
    std::string transition_reason_slug;
};

// This goes inside 'RegionalAvailability'
struct Timeline {
    // The sequence of events for THIS region.
    // Europe: [Active (0-400)] -> [Lost (400-1400)] -> [Active (1400-Present)]
    std::vector<TimeSegment> segments;
};

struct RegionalAvailability {
    // Where is this active?
    std::string historical_region;      // "geo:china", "geo:europe"
    std::string current_region;      // "geo:china", "geo:europe"
    std::string coordinates;      // 52.520008N, 13.404954W

    // When was it active HERE? 
    // Uses the new Timeline system to support "Lost & Found" logic.
    Timeline local_timeline;

    // Provenance
    bool is_indigenous;         // Did it start here?
    std::string import_source;  // If false, where did it come from? ("geo:china")

    // Citations for this specific regional claim
    std::vector<std::string> source_citations;
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
    
    int zoom_level;
    
    // --- Content ---
    std::string wiki_summary;
    std::string image_url;
};

struct OptimizationFactors {
    // 0.0 = No change (Neutral)
    // 1.0 = 2x better (100% improvement)
    // -0.5 = 50% worse (Trade-off)

    float cost_efficiency;   // Making it cheaper
    float production_rate;   // Making it faster (Throughput)
    float quality_reliability; // Making it better/longer lasting
    float size_weight;       // Making it smaller/lighter (Miniaturization)
    float energy_efficiency; // Using less power
    float safety;            // Less likely to kill the user
    float accessibility;     // Lowers the barrier to entry
};

struct LogicGroup {
    // 1. The "Slot" or "Role" (AND)
    // Example: 0 = "Primary Material", 1 = "Catalyst"
    int functional_group_id;
    std::string functional_group_name;

    // 2. The "Option" (OR)
    // Example: For Catalyst, 0 = "Platinum", 1 = "Palladium + Heat"
    int variant_id;
    std::string variant_name;

    // 3. The "Fragment" (AND)
    // Example: If Variant 1 is "Palladium + Heat",
    // Palladium is part_id 0, Heat is part_id 1.
    int part_id;
    std::string part_name;
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
    ValidityStatus validity;
    ResourceCost base_cost; // Aluminum will have edges to multiple things, each will have different costs.

    std::optional<OptimizationFactors> optimization_factor;

    // if this start and ends multiple times have an edge for each instance dont' have a vector here
    std::optional<DatePoint> start_date;
    std::optional<DatePoint> end_date;

    // --- THE LOGIC (The Math) ---
    LogicGroup requirement_logic;

    // --- THE VISUALS (The UI) ---
    // Groups edges together visually (e.g. "Inventors", "Components")
    std::string visual_category_slug;

    // --- Simulation Data ---
    float impact_weight;        // 0.0 - 1.0

    // --- Metadata ---
    std::string justification;
    std::vector<std::string> source_urls;
};