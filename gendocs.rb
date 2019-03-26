require 'graphql-docs'

puts("Generating Docs...")
GraphQLDocs.build(filename: "schema.graphql", delete_output:true, output_dir: "./docs")
puts("Docs Generated")