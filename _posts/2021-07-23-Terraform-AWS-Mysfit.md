---
layout: post
title:  Terraform Series - AWS S3 Buckets, policies and what Terraform can do for us?
excerpt_separator: <!--more-->
---

## Introduction

Hi there, I hope that you are doing well!. In this second blog post about Terraform and AWS I'll try to shared with you what I learned about AWS S3 Buckets and how Terraform can be used to interact with them. This is a brief list of the topics that I plan to cover with today's post:

- A brief introduction of AWS S3
- Differences between IAM Policies, S3 Bucket Policies and S3 ACLs
- Using Terraform to create an S3 Bucket and host a static website
- S3 Bucket policy creation with Terraform
- Applying policies to buckets with Terraform
- Uploading objects to S3 Buckets using Terraform

As you can see we have a long road ahead!. So, let's start.

<!--more-->

The idea for this blog post was born while doing [AWS' "Build a Modern Web Application"](https://aws.amazon.com/getting-started/hands-on/build-modern-app-fargate-lambda-dynamodb-python/module-one/#) hands-on project. Specifically on module I, after setting up an IDE you need to set up an S3 bucket to host an static website. I found this an excellent opportunity to continue learing about Terraform and AWS concepts.

## Fundamental concepts

### AWS Simple Storage Service (S3)

S3 is Amazon's offering to storage data. It allows for uploading and managing arbitrary files. The overall idea is that you (or the users that you allow) can store and retrieve "objects" from "buckets". The most important difference to understand is this is not like a "filesystem" in an OS. In S3, each object (file) has, between other things, a `key` that's unique and identifies the object within the bucket it is stored. Each object has a specific URL that points to it and allow users to interact with them.

There are a lot of interesting details about S3 buckets (what happens with Availability zones, pricing, storage, and so on) that are outside the scope of this blog post. If you have questions about them you can refer to [AWS S3 FAQ](https://aws.amazon.com/s3/faqs/).

### AWS IAM Policies, S3 Bucket policies and S3 ACLs

Now with a brief understaing of S3, I needed to understand how access was granted and forbidden for objects stored in S3 buckets. I found that there are *three (!)* different methods to configure it. Now I understand why so many companies end up having their AWS S3 buckets open to the Internet. It seems to be very easy to screw things up.

By default, when you create a S3 bucket it's configured as `private`. This means that only the owner of the AWS account where the bucket was created can access it. To allow other users to access it a policy is needed.

Broadly speaking, there are two categories for policies. _identity-based_ and _Resource-based_. This means that you can create a policy based on your users, for example, to say: "All users of department X, can access buckets A,B and C. But also you can create policies based on your buckets, and say for example, "bucket Y can be accessible by anyone".

_Note: While reading the documentation I found that AWS supports up to six types of policies: ..."identity-based policies, resource-based policies, permissions boundaries, Organizations SCPs, ACLs, and session policies...". Of course, all the other types beside the two briefly mentioned, are out of the scope of this blog post._

#### Identity and Access Management Policies (IAM)

`IAM policies` are identity-based. IAM policies are objects defined in JSON documents that, when attached to an identity, define what the identity can do. There are two types of `Identity-based` policies:

- Managed (AWS/Customer) policies: They can be attached to multiple users. The difference between "AWS" and "Customer" is that "AWS policies" are managed by AWS and you cannot modify them.
- Inline policies: These policies are only assignable to one identity. Mantain a strict one-to-one relationship and are deleted when you delete the entity that has it assigned. A use case for this can be if at some point you want to create a user with unrestricted privileges and you are worried that the policy for it can be misused and assigned to other users.

#### Bucket policies and bucket ACLs

S3 `bucket policies` and `bucket ACLs` are resource-based. Bucket ACLs are a legacy method to determine who can access buckets and objects in them. AWS recommends using IAM policies or bucket policies. If you want more information about bucket ACLs you can refer to the [documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/acls.html).

Bucket ACLs share the same basic ideas than IAM policies, they are written in JSON documents as well, but are attached to S3 buckets.

### Policies format

Both IAM policies and Bucket policies share the same basic format.

Policies have the following structure:

- Optional policy-wide information (Version and ID)
- One or more statements

#### Statements

Each `statement` determines what the policy allows or denies and from whom (depending the case). Statements contain the following elements:

- Sid (Optional): A name to differentiate each statement.
- Effect: It can be "Allow" or "Deny".
- Principal: Only used in case a resource-based policy is created. It contains the user, or role for whom the policy applies.
- Action: List of actions that are allowed or denied.
- Resource: Only used in case a identity-bsed policy is created. It contains which resources the user or role will be able to apply the actions listed in the policy.
- Condition (Optional): Specific cirmcumnstances under which the policy grants permisssion. For example you could set up a policy that additionaly checks for the IP address of an user to do an action.

### Creating an S3 bucket with Terraform

Well... after a long, but necesary introduction to core concepts we can start the fun part. I needed to understand how to create a S3 bucket using Terraform. I created a new file called `main.tf` that contained the text below.

Also bear in mind that all the code shown in this blog post can be found here: [https://github.com/nahueldsanchez/terraform-s3-bucket-mysfits](https://github.com/nahueldsanchez/terraform-s3-bucket-mysfits)

```
...

resource "aws_s3_bucket" "aws-mysfits-terraform" {
    bucket = var.s3_bucket_name

    website {
        index_document = "index.html"
    }
}

resource "aws_s3_bucket_object" "s3-upload-index" {
    bucket = aws_s3_bucket.aws-mysfits-terraform.id
    key = "index.html"
    content_type = "text/html"
    source = "${var.github_project_path}/module-1/web/index.html"
}

output "s3-domain-name" {
    value = aws_s3_bucket.aws-mysfits-terraform.website_endpoint
}
```

For the sake of clarity I ommited the provider declaration part. As you can see, I created an `aws_s3_bucket` resource called `aws-mysfits-terraform`. This resource has an optional argument called `bucket` which is used to set the bucket's name. In my case I defined a variable, `s3_bucket_name`, in a file called `variables.tf` that's used here.

I used a specific property of the bucket that allows it to store a static website. You can find more information about that here: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EnableWebsiteHosting.html. To do that in Terraform, I used the `website` object.

The `website` object has an `index_document` argument that stablishes what file is returned when an HTTP(s) request arrives to the root of the S3 bucket. In my case I chose the `index.html` file that I will upload.

### Uploading a file to the previously created S3 bucket.

The next step was to upload the `index.html` file. using the following code (copying it below for clarity):

```
resource "aws_s3_bucket_object" "s3-upload-index" {
    bucket = aws_s3_bucket.aws-mysfits-terraform.id
    key = "index.html"
    content_type = "text/html"
    source = "${var.github_project_path}/module-1/web/index.html"
}
```

for that I chose to use the `aws_s3_bucket_object` resource. This resource allows to upload only one file, but so far, is enough. It is possible to upload multiple files using some Terraform magic, but that's material for other blog post.

The `aws_s3_bucket_object` has the following arguments:

- bucket: Bucket to put the file in. I'm using the `id` of the bucket previously created.
- key: Name of the file in the bucket.
- content_type: Used to set the type of the file when retrieved by the browser. We need `"text/html"` for the browser to properly render our HTML file.
- source: Local path to the file. I'm using [Terraform's Interpolation syntax](https://www.terraform.io/docs/configuration-0-11/interpolation.html) to join the value of a variable called `github_project_path` with an string `/module-1/web/index.html`. This ends up being resolved as: `/home/user/repo/aws-modern-application-workshop//module-1/web/index.html`.

Doing a quick recap, so far we have our S3 Bucket created and a file already uploaded, but by default no one except the Bucket owner will be able to access it. That's not useful if we plan to have a public website there. We need to write a policy to change this. Let's see how to do it in the next section.

## Terraform and IAM policies

Terraform has a resource called [`aws_iam_policy`](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) that can be used to create the policy we need. We will create a bucket policy to allow any user to access the files stored in the bucket. An example of this resource can be seen below:

```
resource "aws_iam_policy" "policy" {
  name        = "PolicyName"
  description = "PolicyDescription"

  # Policy content
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:Describe*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
```

As you can see its use is very straightforward, but having to embed policies in the resource definition has some limitations:

1. Keeping policies versioned will be difficult.
2. Sintax errors included in the policy won't be noticed by Terraform.

### Terraform Data Source: IAM Policy Document

To help with this Terraform provides a Data Source called [`aws_iam_policy_document`](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document), that allows you to write a IAM policy using Hashicorp's Configuration Language enjoying sintax checking and making it easier to reutilize policies.

To use it, I created a file called `bucket_policy.tf` with the following content:

```
data "aws_iam_policy_document" "aws_bucket_policy_document" {
    statement {
        sid = "PublicReadForGetBucketObjects"
        effect = "Allow"

        principals {
            type = "*"
            identifiers = ["*"]
        }

        actions = [
            "s3:GetObject"
        ]

        resources = [
            "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
    }

}

resource "aws_s3_bucket_policy" "mysfits-s3-policy" {
    bucket = aws_s3_bucket.aws-mysfits-terraform.id
    policy = data.aws_iam_policy_document.aws_bucket_policy_document.json
}
```
The policy document shares a lot of similarities with an IAM policy. In this case I included a `principals` block with `identifiers` = `[*]` to allow any user to access the bucket. I added the bucket previously created to the `resources` block and appended `/*` to allow to retrieve (Amazon action `s3:GetObject`) any file from it.

The last resource `aws_s3_bucket_policy` is the one doing the trick. It attaches the policy document previously created to the bucket created in the previous section.

With this we have everything we need to test our Terraform deployment. We need to run `terraform init` and `terraform plan`. If we are OK with everything we run `terraform apply`. The `main.tf` file has an output declared to print the bucket domain name. If everything went well you'll see it in the console. You can access it with your browser to test it.

I hope that you enjoyed the blog post!. Thanks for your time reading it and stay tuned for more content.

## References

- S3 IAM Policies vs S3 Bucket Policies vs S3 ACLs - https://aws.amazon.com/blogs/security/iam-policies-and-bucket-policies-and-acls-oh-my-controlling-access-to-s3-resources/
- IAM Policies - https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html
- Identity based policies - https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_id-based
- Resource based policies - https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_resource-based
- S3 ACLs - https://docs.aws.amazon.com/AmazonS3/latest/userguide/acls.html
- S3 IAM Policies vs S3 Bucket Policies vs S3 ACLs (https://aws.amazon.com/blogs/security/iam-policies-and-bucket-policies-and-acls-oh-my-controlling-access-to-s3-resources/)
- Principal in AWS JSON Policy - https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
- Resource in AWS JSON Policy - https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_resource.html
- Terraform AWS S3 Bucket Resource - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket#website
- Terraform AWS S3 Bucket object Resource - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_object
- Terraform S3 object Resource - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_object
- Writing an IAM policy in Terraform - https://learn.hashicorp.com/tutorials/terraform/aws-iam-policy
- IAM Policy document Terraform - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document
- S3 Bucket policy terraform - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy
