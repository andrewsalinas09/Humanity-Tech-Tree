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
    // THE ORTHOGONAL BASIS (ADR-0024/0028). Types are the traversal partition
    // key: a type exists only if a traverser at a high-fan-out node needs it
    // to prune, or a machine consumer treats it differently. ALL flavor lives
    // in DependencyEdge::qualifier. Adding a type requires an ADR proving a
    // new pruning need or machine behavior. Legacy->basis mapping: ADR-0028.

    ENABLES,           // Existence dependency; possibility traversal.
                       // Counterfactual mode masks works/people (ADR-0025).
                       // Absorbs DEPENDENT_FOR, SPECIFIES_STANDARD (target
                       // category prunes), KNOWLEDGE_REQUIREMENT (linter:
                       // BIOLOGICAL_ENTITY only receives knowledge ENABLES).

    IS_COMPONENT_OF,   // Assembled part ("Lens" -> "Telescope"); BOM counting.
    IS_INGREDIENT_OF,  // Consumed/transformed input ("Glass" -> "Lens").
                       // Distinct from component: "made from" vs "contains"
                       // are different constantly-asked questions (DuPont).

    IS_TYPE_OF,        // Classification; inheritance flows down (ADR-0019).
    IS_REFINEMENT_OF,  // Version/generation walks; flat stars (ADR-0018).

    OPTIMIZES,         // Improves attributes; existence dead-end (ADR-0006).

    SUCCEEDS,          // Dated succession story; timeline-wave rendering.
                       // qualifier: replaced, superseded, spun-off,
                       // rebranded, forked, merged.

    ASSOCIATION,       // Story/attribution ghost layer; solver-invisible.
                       // qualifier: authored, discovered, invented, founded,
                       // influenced, studied-at, disproved, suppresses,
                       // motivated, drives-need, precipitated, gave-rise-to,
                       // funded, codifies, custody, brand-applies, ...
                       // Split later by qualifier if profiling demands it.
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

// [KEPT] The State Machine is still needed to calculate if an Abstract Node
// is "Real" (has working children) or "Theoretical" (has no working children).
enum class NodeState {
    LOCKED,         // Impossible (Physics/Parents missing).
    THEORETICAL,    // Concept valid, but no Instances are working. (Vaporware)
    REALIZED        // Concept valid + >0 Instances are functional.
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
// 5. DYNAMIC ATTRIBUTE SYSTEM (NEW)
// ==========================================
// Handles the "Process Modifiers" and "Infinite Attributes" logic efficiently.

using AttributeID = uint32_t;
using AttributeValue = std::variant<double, std::string, int>; // Can expand if needed

// Operations for Process Nodes (How they change the material)
enum class ModifierType {
    SET_VALUE,      // Overwrite (e.g., Purity = 0.999)
    ADD_VALUE,      // Accumulate (e.g., Cost += 10)
    MULTIPLY_VALUE  // Scale (e.g., Strength *= 1.5)
};

// Comparators for Edges (How they check the material)
enum class ConstraintOp {
    GREATER_THAN,
    LESS_THAN,
    EQUAL_TO,
    CONTAINS // For string flags
};

struct AttributeModifier {
    AttributeID attribute_id;
    AttributeValue value;
    ModifierType type;
};

struct AttributeConstraint {
    AttributeID attribute_id;
    AttributeValue target_value;
    ConstraintOp operation;
};

// The Registry should be a Singleton in your App Logic, used to look up IDs.
// Including the declaration here for context.
/*
class AttributeRegistry {
public:
    AttributeID getID(const std::string& name);
    std::string getName(AttributeID id);
};
*/

// Requirement logic (ADR-0017): a boolean expression tree over the consumer
// node's incoming dependency edge IDs. Leaves reference edges; AND/OR/NOT nest
// arbitrarily. Absent tree = AND of all hard dependency edges. NOT is legal but
// discouraged — it breaks the monotonicity that makes incomplete graphs safe.
// Example: OR( platinum_edge, AND( palladium_edge, heat_edge ) )
struct RequirementExpr {
    enum class Op { EDGE, AND, OR, NOT };
    Op op = Op::EDGE;
    std::string edge_id;                    // when op == EDGE
    std::vector<RequirementExpr> children;  // when op != EDGE
};

// ADR-0019: instance-level overrides of inherited family edges.
// Family edges are inheritable defaults; instances may WIDEN (relax the
// requirement to the LCA, per ADR-0008) or EXCLUDE (the default does not
// apply here). NOTE: EXCLUDE is "does not inherit", which is NOT the same
// as RequirementExpr NOT ("requires the absence of").
struct InheritanceOverride {
    std::string family_edge_id;
    enum class Kind { WIDEN_TO_LCA, EXCLUDE };
    Kind kind;
    std::string relaxed_target_id;  // WIDEN_TO_LCA only
    std::string justification;
};

// ==========================================
// 3. THE NODE
// ==========================================

struct HistoryNode {
    // --- Identity ---
    std::string primary_id;             // UUID Instead of having iphone 16 be a shub id to iphone it will simply be a child node with edge refins etc...
    std::string wikidata_id;    // "Q12345"
    std::string slug;           // "steam-engine"

    // --- Core Data ---
    std::string name;
    std::vector<std::string> aliases;

    // ADR-0022: dated names for rebrands (Twitter 2006-2023, X 2023-).
    // Lazy — empty until a rebrand happens. Aliases stay undated search keys.
    struct DatedName { std::string name; std::optional<DatePoint> start, end; };
    std::vector<DatedName> name_history;
    NodeCategory category;
    ValidityStatus validity;


    NodeState current_state = NodeState::REALIZED;
    int active_instance_count = 0;


    // --- Simulation Properties ---
    // This vector handles the "Gunpowder" problem.
    // One node, multiple start dates depending on location.
    std::vector<RegionalAvailability> availability;

    int zoom_level;

    // --- Content ---
    std::string wiki_summary;
    std::string image_url;

std::unordered_map<AttributeID, AttributeValue> base_attributes;
std::unordered_map<std::string, std::vector<AttributeModifier>> process_output_effects;

    // ADR-0017: boolean expression tree over incoming dependency edges.
    // std::nullopt = AND of all hard dependency edges (the common case).
    std::optional<RequirementExpr> requirement_expr;

    // ADR-0019: this instance's deviations from inherited family edges.
    // Effective deps = own edges + inherited edges - exclusions, widenings applied.
    // Inherited-but-unasserted facts are PRESUMPTIONS (render distinctly).
    std::vector<InheritanceOverride> inheritance_overrides;
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


// ==========================================
// 4. THE EDGE
// ==========================================

struct DependencyEdge {
    std::string id;
    std::string from_node_id;
    std::string to_node_id;

    EdgeType type;
    // ADR-0024: the flavor slug ("spun-off", "authored", "drives-need"...).
    // Carries all meaning that never needs to prune a traversal.
    // LLM-canonicalized like attribute names; secondary-indexed for search.
    std::string qualifier;

    // ADR-0027: two orthogonal truth axes. Validity = is the claim's content
    // held true today; Epistemic = how confident are we the record is
    // accurate. Phlogiston edges: well-documented (epistemic) AND disproven
    // (validity) — mergeable into neither single scale.
    EpistemicStatus truth_level;
    ValidityStatus validity;
    ResourceCost base_cost; // Aluminum will have edges to multiple things, each will have different costs.

    std::optional<OptimizationFactors> optimization_factor;

    // if this start and ends multiple times have an edge for each instance dont' have a vector here
    std::optional<DatePoint> start_date;
    std::optional<DatePoint> end_date;

    // Requirement logic lives on the consumer node (ADR-0017), not on edges.

    // ADR-0021: finer edges that fully cover this edge's claim. Empty = live.
    // Shadowed edges stay true; counting/BOM queries skip them, truth queries
    // don't. Re-validated whenever a covering edge changes.
    std::vector<std::string> shadowed_by_edge_ids;

    std::vector<AttributeConstraint> constraints;

    // --- THE VISUALS (The UI) ---
    // Groups edges together visually (e.g. "Inventors", "Components")
    std::string visual_category_slug;

    // --- Simulation Data ---
    float impact_weight;        // 0.0 - 1.0

    // --- Metadata ---
    std::string justification;
    std::vector<std::string> source_urls;
};