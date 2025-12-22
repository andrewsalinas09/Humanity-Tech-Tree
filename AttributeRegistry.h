#include <string>
#include <unordered_map>
#include <vector>
#include <mutex>

// ==========================================
// THE ROSETTA STONE
// ==========================================
// Converts strings ("Voltage") to ints (42) for speed.
// Thread-safe so the simulation can run on multiple cores.

class AttributeRegistry {
public:
    using AttributeID = uint32_t;

    // Singleton Access
    static AttributeRegistry& instance() {
        static AttributeRegistry instance;
        return instance;
    }

    // 1. Get the ID (Creates it if it doesn't exist)
    // FAST - used during Graph Building
    AttributeID getID(const std::string& name) {
        std::lock_guard<std::mutex> lock(registry_mutex);

        // If we already know this attribute, return its ID
        if (id_map.find(name) != id_map.end()) {
            return id_map[name];
        }

        // Otherwise, register a new one
        AttributeID new_id = next_id++;
        id_map[name] = new_id;
        name_map[new_id] = name;
        return new_id;
    }

    // 2. Get the Name (For UI / Debugging)
    // SLOW - used only when showing data to the user
    std::string getName(AttributeID id) {
        std::lock_guard<std::mutex> lock(registry_mutex);
        if (name_map.find(id) != name_map.end()) {
            return name_map[id];
        }
        return "UNKNOWN_ATTRIBUTE";
    }

private:
    // Private Constructor (Singleton)
    AttributeRegistry() = default;

    std::unordered_map<std::string, AttributeID> id_map;
    std::unordered_map<AttributeID, std::string> name_map;
    uint32_t next_id = 1; // Start at 1 so 0 can be "NULL"
    std::mutex registry_mutex;
};