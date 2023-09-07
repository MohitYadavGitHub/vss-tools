from neo4j import GraphDatabase
from vspec.model.vsstree import VSSNode
import argparse

def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "The csv exporter does not support any additional arguments."


class VSSNeo4jExporter:

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def _add_node(self, tx, node_id, properties):
        node_type = properties.get("type")
        nodeLabel = f"VSSNode_{node_type}"
        # Remove 'type' as you mentioned it doesn't need to be an attribute of the created node.
        del properties['type']
        query = f"""
        CREATE (a:{nodeLabel} {{id: $id, name: $name, uuid: $uuid, min: $min, max: $max}})
        """
        tx.run(query, id=node_id, **properties)


    def _add_relationship(self, tx, parent_type, parent_id, child_type, child_id):
        # Create an "IsAChild" relationship between parent and child nodes
        query = f"""
        MATCH (a:{parent_type}), (b:{child_type}) 
        WHERE a.id = $parent_id AND b.id = $child_id 
        CREATE (a)-[r:IsAChild]->(b)
        """
        tx.run(query, parent_id=parent_id, child_id=child_id)

    def export_node(self, node):
        with self._driver.session() as session:
            # Export this node
            properties = {
                "name": node.name,
                "uuid": node.uuid,
                "min": node.min,
                "max": node.max,
                "type": str(node.type.value)
                # ... (add other attributes) Enough for the PoC
            }
            session.write_transaction(self._add_node, id(node), properties)

            # First create all child nodes
            for child in node.children:
                self.export_node(child)

            # Then create relationships to child nodes
            for child in node.children:
                parent_type = f"VSSNode_{node.type.value}"
                child_type = f"VSSNode_{child.type.value}"
                session.write_transaction(self._add_relationship, parent_type, id(node), child_type, id(child))


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid, ):
    uri="bolt://localhost:7687"   ### the info below would need to be changed ofcourse to your instance
    user="neo4j"   ## secrets in plain text bad. use your Solution, (Ex: Vault)
    password="password"
    exporter = VSSNeo4jExporter(uri, user, password)
    exporter.export_node(signal_root)
    exporter.close()

if __name__ == "__main__":
    print (' ok Came here')
    pass
    # # Assume you have a root VSSNode object
    # root = VSSNode("Root", None, ...)

    # # Export VSS tree to Neo4j
    # export(root)
