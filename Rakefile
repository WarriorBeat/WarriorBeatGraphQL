# Rakefile for handling docs and aws-exports

require 'graphql-docs'
require 'gist'
require 'fileutils'
require 'colored'

AWS_EXPORTS=File.join(Dir.pwd, "amplify/aws-exports.js").freeze


# Generates GraphQl Api Docs
task :gendoc do
    puts("Generating Docs...".cyan)
    GraphQLDocs.build(filename: "schema.graphql", delete_output:true, output_dir: "./docs", base_url:"/WarriorBeatGraphQL")
    puts("Docs Generated".bold.green)
end

# Upload AWS Exports to Gist
task :upload_exports do
    puts("Uploading AWS Exports...".cyan)
    puts("Gist ID: #{ENV['AWS_EXPORTS_GIST_ID']}".yellow)
    content = File.read(AWS_EXPORTS)
    Gist.gist(content, filename:"aws-exports.js", update: ENV['AWS_EXPORTS_GIST_ID'], public:false)
    puts("Done!".bold.green)
end
